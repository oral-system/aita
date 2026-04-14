from django.db import models
from django.conf import settings
# 核心：引用 DMOJ 既有模型
from judge.models import Problem, ProblemGroup, Submission 

# ============================================================
# 模組一：使用者與權限管理 (整合 DMOJ User)
# ============================================================

class Role(models.Model):
    role_name = models.CharField(max_length=50, verbose_name='角色名稱')
    class Meta:
        db_table = 'Roles'
    def __str__(self):
        return self.role_name

class UserProfile(models.Model):
    """擴充 DMOJ 的 User 資訊"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='oral_profile')
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    student_id = models.CharField(max_length=20, unique=True, null=True, blank=True, verbose_name='學號')
    class Meta:
        db_table = 'User_Profiles'

# ============================================================
# 模組二：教材與出題限制 (你的核心功能：教材連結範圍)
# ============================================================

class Material(models.Model):
    problem_group = models.ForeignKey(
        ProblemGroup, on_delete=models.CASCADE, related_name='materials'
    )
    file_name = models.CharField(max_length=255, verbose_name='教材名稱')
    
    # ✅ 關鍵：必須有這個欄位，views.py 才能執行 file=uploaded_file
    file = models.FileField(upload_to='materials/', verbose_name='實體檔案', null=True)
    
    # 保留這個欄位存路徑也沒關係
    file_path = models.CharField(max_length=500, verbose_name='檔案路徑', blank=True)

    class Meta:
        db_table = 'Materials'

class MaterialTopic(models.Model):
    """教材勾選章節表"""
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='topics')
    topic_name = models.CharField(max_length=200, verbose_name='章節名稱')
    class Meta:
        db_table = 'Material_Topics'

class Constraint(models.Model):
    """解題限制設定 (依據教材進度)"""
    # 這裡連結到下方的 SubProblem
    sub_problem = models.OneToOneField('SubProblem', on_delete=models.CASCADE, related_name='constraint')
    ask_out_of_scope_first = models.BooleanField(default=False, verbose_name='超出教材範圍時優先詢問')
    reject_banned_syntax = models.BooleanField(default=False, verbose_name='使用禁用寫法時不給測驗')
    class Meta:
        db_table = 'Constraints'

class BannedSyntax(models.Model):
    """禁用語法明細 (例如：這週不准用 math 函式庫)"""
    constraint = models.ForeignKey(Constraint, on_delete=models.CASCADE, related_name='banned_syntaxes')
    syntax_type = models.CharField(max_length=50, choices=[('Import', 'Import 引用'), ('Keyword', 'Keyword 語法')])
    syntax_name = models.CharField(max_length=100, verbose_name='禁用名稱')
    class Meta:
        db_table = 'Banned_Syntaxes'

# ============================================================
# 模組三：口試核心設定 (擴充 DMOJ Problem)
# ============================================================

class CognitiveType(models.Model):
    TYPE_CHOICES = [('Memory', '記憶'), ('Understanding', '理解'), ('Application', '應用'), ('Analysis', '分析')]
    type_name = models.CharField(max_length=50, choices=TYPE_CHOICES)
    class Meta:
        db_table = 'Cognitive_Types'
    def __str__(self):
        return self.get_type_name_display()

class SubProblem(models.Model):
    """口試專用參數表：OneToOne 連結 DMOJ 題目"""
    problem = models.OneToOneField(
        Problem, on_delete=models.CASCADE, primary_key=True, related_name='oral_settings'
    )
    # 你要求的四大核心欄位
    solution_limit = models.TextField(blank=True, verbose_name='解題限制')
    concepts_and_solutions = models.TextField(blank=True, verbose_name='觀念與解法')
    resources_algorithms = models.TextField(blank=True, verbose_name='題目資源/算法')
    ai_analysis_text = models.TextField(null=True, blank=True, verbose_name='AI 題意解析')
    
    exam_time_limit = models.PositiveIntegerField(default=10)
    oral_percentage = models.PositiveSmallIntegerField(default=30)
    filter_ref = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='濾數設定')

    class Meta:
        db_table = 'Oral_SubProblems'

# ============================================================
# 模組四：AI 邏輯與場次管理 (保留原邏輯)
# ============================================================

class QuestionTemplate(models.Model):
    template_name = models.CharField(max_length=100)
    prompt_content = models.TextField()
    class Meta:
        db_table = 'Question_Templates'

class FrameworkSetting(models.Model):
    sub_problem = models.ForeignKey(SubProblem, on_delete=models.CASCADE)
    cognitive_type = models.ForeignKey(CognitiveType, on_delete=models.PROTECT)
    template = models.ForeignKey(QuestionTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    question_count = models.PositiveSmallIntegerField(default=1)
    class Meta:
        db_table = 'Framework_Settings'

class OralSession(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.PROTECT)
    session_name = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    class Meta:
        db_table = 'Oral_Sessions'

class SessionRegistration(models.Model):
    session = models.ForeignKey(OralSession, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    attendance_status = models.CharField(max_length=10, default='Pending')
    class Meta:
        db_table = 'Session_Registrations'

# ============================================================
# 模組五：對話、紀錄與評分 (與 DMOJ Submission 連動)
# ============================================================

class OralRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    sub_problem = models.ForeignKey(SubProblem, on_delete=models.PROTECT)
    # 連結到 DMOJ 的繳交紀錄
    dmoj_submission = models.ForeignKey(Submission, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=15, default='In_Progress')
    start_time = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'Oral_Records'

class ChatMessage(models.Model):
    oral_record = models.ForeignKey(OralRecord, on_delete=models.CASCADE)
    sender_type = models.CharField(max_length=10, choices=[('AI', 'AI'), ('Student', '學生')])
    message_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'Chat_Messages'

class StudentScore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    problem = models.ForeignKey(Problem, on_delete=models.PROTECT)
    base_score = models.IntegerField(default=0)
    oral_score = models.IntegerField(default=0)
    final_score = models.IntegerField(default=0)
    class Meta:
        db_table = 'Student_Scores'
        unique_together = [('user', 'problem')]
    def save(self, *args, **kwargs):
        self.final_score = self.base_score + self.oral_score
        super().save(*args, **kwargs)