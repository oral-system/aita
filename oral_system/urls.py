from django.urls import path
from . import views 

urlpatterns = [
    path('', views.home, name='oral_home'),
    path('list/', views.change_list, name='change_list'),
    path('api/subproblems/', views.get_subproblems_api, name='subproblems_api'),
    path('api/materials/', views.get_materials_api, name='get_materials_api'),
    path('api/materials/upload/', views.upload_material_api, name='upload_material_api'),
    path('sub/<int:sub_id>/solution/', views.set_solution_rule, name='solution_rule'),
    path('sub/<int:sub_id>/edit/', views.view_and_edit, name='view_and_edit'),
    path('api/testcases/', views.get_problem_testcases, name='get_problem_testcases'),
]
