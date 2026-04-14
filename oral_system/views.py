import os
import re
import zipfile
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from judge.models import Problem, ProblemGroup
from .models import Material, SubProblem


def home(request):
    context = {'title': '口試系統'}
    return render(request, 'oral_system/oral_home.html', context)

@staff_member_required
def change_list(request):
    """建置框架主頁面"""
    problems = ProblemGroup.objects.all()
    selected_id = request.GET.get('problem', '')
    selected_group = None
    subproblems = []

    if selected_id:
        selected_group = get_object_or_404(ProblemGroup, id=selected_id)
        # 2. 修正：欄位名稱是 group (單數)
        subproblems = Problem.objects.filter(group=selected_group)

    context = {
        'problems': problems,
        'selected_problem': selected_group,
        'subproblems': subproblems,
        'title': '建置框架',
        'has_permission': True,
    }
    return render(request, 'oral_system/oral_frame.html', context)

@staff_member_required
def get_subproblems_api(request):
    """AJAX API：根據分類 ID 回傳題目清單"""
    group_id = request.GET.get('problem', '')
    try:
        group = ProblemGroup.objects.get(id=group_id)
        # 3. 修正：這裡同樣改為 group=group
        subs = list(Problem.objects.filter(group=group).values('id', 'code', 'name'))
        return JsonResponse({'status': 'ok', 'subproblems': subs})
    except (ProblemGroup.DoesNotExist, ValueError):
        return JsonResponse({'status': 'error', 'subproblems': []})

@staff_member_required
def get_materials_api(request):
    """獲取該大題分類下的所有教材"""
    group_id = request.GET.get('group_id')
    if not group_id:
        return JsonResponse({'status': 'error', 'msg': '無分類 ID'})
    
    # 抓取屬於該群組的所有教材
    materials = Material.objects.filter(problem_group_id=group_id).values('id', 'file_name')
    return JsonResponse({'status': 'ok', 'materials': list(materials)})

@staff_member_required
def upload_material_api(request):
    """上傳教材並連結至大題分類"""
    if request.method == 'POST' and request.FILES.get('file'):
        group_id = request.POST.get('group_id')
        uploaded_file = request.FILES['file']
        
        # 建立紀錄
        material = Material.objects.create(
            problem_group_id=group_id,
            file=uploaded_file,
            file_name=uploaded_file.name
        )
        return JsonResponse({'status': 'ok', 'id': material.id, 'name': material.file_name})
    return JsonResponse({'status': 'error'})

@staff_member_required
def set_solution_rule(request, sub_id):
    """解題規則設定"""
    return render(request, 'oral_system/placeholder.html', {'title': '解題規則設定'})

@staff_member_required
def view_and_edit(request, sub_id):
    """檢視及修改"""
    return render(request, 'oral_system/placeholder.html', {'title': '檢視及修改'})

@staff_member_required
def get_problem_testcases(request):
    problem_code = request.GET.get('code', '')
    if not problem_code:
        return JsonResponse({'status': 'error', 'msg': '無題目代號'})

    # 1. 基礎路徑定義
    base_path = f"/home/kiogh/judge-server/problems/{problem_code}"
    # 【修正】：必須先定義 zip_path，後面的 if 才能判斷
    zip_path = os.path.join(base_path, f"{problem_code}.zip")
    
    testcases = []

    # 2. 優先嘗試讀取 ZIP 壓縮檔 (DMOJ 標準儲存方式)
    if os.path.exists(zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                all_files = z.namelist()
                in_files = sorted([f for f in all_files if f.endswith('.in')])
                for in_f in in_files:
                    prefix = in_f.replace('.in', '')
                    out_f = f"{prefix}.out"
                    
                    with z.open(in_f) as f:
                        in_content = f.read(100).decode('utf-8', errors='ignore')
                    
                    out_content = ""
                    if out_f in all_files:
                        with z.open(out_f) as f:
                            out_content = f.read(100).decode('utf-8', errors='ignore')
                            
                    testcases.append({
                        'num': os.path.basename(prefix),
                        'input': in_content,
                        'output': out_content
                    })
            # 如果 ZIP 讀取成功且有東西，直接回傳
            if testcases:
                return JsonResponse({'status': 'ok', 'testcases': testcases})
        except Exception as e:
            # ZIP 讀取失敗時記錄錯誤，但不中斷，嘗試讀取資料夾
            print(f"ZIP 讀取失敗: {e}")

    # 3. 備案：讀取資料夾下的散裝檔案 (如果你手動解壓縮過)
    if os.path.exists(base_path):
        try:
            files = os.listdir(base_path)
            in_files = sorted([f for f in files if f.endswith('.in')])
            
            for in_file in in_files:
                prefix = os.path.splitext(in_file)[0]
                out_file = f"{prefix}.out"
                
                # 讀取 .in
                with open(os.path.join(base_path, in_file), 'r', encoding='utf-8', errors='ignore') as f:
                    in_content = f.read(100) 
                
                # 讀取 .out
                out_content = ""
                out_path = os.path.join(base_path, out_file)
                if os.path.exists(out_path):
                    with open(out_path, 'r', encoding='utf-8', errors='ignore') as f:
                        out_content = f.read(100)
                
                testcases.append({
                    'num': prefix,
                    'input': in_content,
                    'output': out_content
                })
        except Exception as e:
            return JsonResponse({'status': 'error', 'msg': f'讀取資料夾失敗: {str(e)}'})

    # 最後回傳結果
    if not testcases:
        return JsonResponse({'status': 'ok', 'testcases': [], 'msg': '找不到任何測資檔案'})
        
    return JsonResponse({'status': 'ok', 'testcases': testcases})