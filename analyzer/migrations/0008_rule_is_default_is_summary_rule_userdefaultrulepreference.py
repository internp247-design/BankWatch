# Generated migration for adding default rule support

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('analyzer', '0007_transaction_edited_by_transaction_is_manually_edited_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='rule',
            name='is_default',
            field=models.BooleanField(default=False, help_text='Mark as default rule to auto-apply on results page'),
        ),
        migrations.AddField(
            model_name='rule',
            name='is_summary_rule',
            field=models.BooleanField(default=False, help_text='Marks aggregation rules (Total Credit/Debit/etc)'),
        ),
        migrations.CreateModel(
            name='UserDefaultRulePreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('defaults_enabled', models.BooleanField(default=True, help_text='Enable auto-apply of default rules on results page')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='default_rule_preference', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Default Rule Preference',
                'verbose_name_plural': 'User Default Rule Preferences',
            },
        ),
    ]
