from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    # Redirect /analyzer/ to /analyzer/dashboard/
    path('', RedirectView.as_view(url='dashboard/', permanent=False), name='analyzer_index'),
    
    # Dashboard and core functionality
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_statement, name='upload_statement'),
    path('results/<int:statement_id>/', views.analysis_results, name='analysis_results'),
    path('create-account/', views.create_first_account, name='create_first_account'),
    path('accounts/create/', views.create_account, name='create_account'),
    path('accounts/<int:account_id>/view/', views.view_account_details, name='view_account_details'),
    path('accounts/<int:account_id>/delete/', views.delete_account, name='delete_account'),
    
    # Unified Create Your Own Page
    path('create-your-own/', views.create_your_own, name='create_your_own'),
    
    # AJAX Endpoints for Create Your Own
    path('api/rule/create/', views.create_rule_ajax, name='create_rule_ajax'),
    path('api/rule/<int:rule_id>/get/', views.get_rule_ajax, name='get_rule_ajax'),
    path('api/rule/<int:rule_id>/update/', views.update_rule_ajax, name='update_rule_ajax'),
    path('api/category/create/', views.create_category_ajax, name='create_category_ajax'),
    path('api/category/<int:category_id>/edit/', views.update_category_ajax, name='update_category_ajax'),
    path('api/category/<int:category_id>/conditions/', views.get_category_conditions_ajax, name='get_category_conditions_ajax'),
    path('api/category/<int:category_id>/delete/', views.delete_category_ajax, name='delete_category_ajax'),
    path('api/rule/<int:rule_id>/delete/', views.delete_rule_ajax, name='delete_rule_ajax'),
    path('api/category-rule/<int:rule_id>/delete/', views.delete_category_rule_ajax, name='delete_category_rule_ajax'),
    
    # Rules Engine URLs (keep for backward compatibility)
    path('rules/', views.rules_list, name='rules_list'),
    path('rules/create/', views.create_rule, name='create_rule'),
    path('rules/<int:rule_id>/edit/', views.edit_rule, name='edit_rule'),
    path('rules/<int:rule_id>/delete/', views.delete_rule, name='delete_rule'),
    path('rules/apply/', views.apply_rules, name='apply_rules'),
    path('rules/apply/results/', views.rules_application_results, name='rules_application_results'),
    path('rules/categorized/', views.rules_categorized, name='rules_categorized'),
    path('rules/test/', views.test_rules, name='test_rules'),
    path('rules/toggle-active/', views.toggle_rule_active, name='toggle_rule_active'),
    path('rules/change-status/', views.change_rule_status_on_results, name='change_rule_status_on_results'),
    
    # Statement-specific rules
    path('statements/<int:statement_id>/rules-prompt/', views.statement_rules_prompt, name='statement_rules_prompt'),
    
    # Custom Categories
    path('custom-categories/create/', views.create_custom_category_and_rule, name='create_custom_category'),
    path('custom-categories/<int:category_id>/rule/', views.create_custom_category_rule, name='create_custom_category_rule'),
    path('custom-categories/', views.custom_categories_list, name='custom_categories_list'),
    path('custom-categories/<int:category_id>/delete/', views.delete_custom_category, name='delete_custom_category'),
    path('custom-categories/rule/<int:rule_id>/edit/', views.edit_custom_category_rule, name='edit_custom_category_rule'),
    path('custom-categories/rule/<int:rule_id>/delete/', views.delete_custom_category_rule, name='delete_custom_category_rule'),
    path('statements/<int:statement_id>/apply-custom-category/', views.apply_custom_category, name='apply_custom_category'),
    path('apply-custom-category-rules/', views.apply_custom_category_rules, name='apply_custom_category_rules'),
    path('api/financial-overview/', views.get_financial_overview_data, name='get_financial_overview_data'),
    path('export/rules-results/', views.export_rules_results_to_excel, name='export_rules_results'),
    path('export/rules-results-pdf/', views.export_rules_results_to_pdf, name='export_rules_results_pdf'),
    path('export/rules-results-pdf-ajax/', views.export_rules_results_ajax_pdf, name='export_rules_results_ajax_pdf'),
    path('export/rules-results-excel-ajax/', views.export_rules_results_ajax_excel, name='export_rules_results_ajax_excel'),
]