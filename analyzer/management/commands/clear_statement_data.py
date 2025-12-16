"""
Management command to clear old statement data from the database.

Usage:
    python manage.py clear_statement_data --help
    python manage.py clear_statement_data --all
    python manage.py clear_statement_data --transactions
    python manage.py clear_statement_data --statements
    python manage.py clear_statement_data --accounts
    python manage.py clear_statement_data --before YYYY-MM-DD
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from analyzer.models import BankAccount, BankStatement, Transaction


class Command(BaseCommand):
    help = 'Clear old bank statement data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear all data (transactions, statements, and accounts)',
        )
        
        parser.add_argument(
            '--transactions',
            action='store_true',
            help='Clear all transactions only',
        )
        
        parser.add_argument(
            '--statements',
            action='store_true',
            help='Clear all statements only',
        )
        
        parser.add_argument(
            '--accounts',
            action='store_true',
            help='Clear all accounts',
        )
        
        parser.add_argument(
            '--before',
            type=str,
            help='Clear data before specific date (format: YYYY-MM-DD)',
        )
        
        parser.add_argument(
            '--days',
            type=int,
            help='Clear data older than N days',
        )
        
        parser.add_argument(
            '--user',
            type=int,
            help='Clear data for specific user ID only',
        )
        
        parser.add_argument(
            '--account',
            type=int,
            help='Clear data for specific account ID only',
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )

    def handle(self, *args, **options):
        # Check if at least one action is specified
        if not any([options['all'], options['transactions'], options['statements'], 
                    options['accounts'], options['before'], options['days']]):
            self.stdout.write(
                self.style.ERROR(
                    'Error: Please specify an action (--all, --transactions, '
                    '--statements, --accounts, --before, or --days)'
                )
            )
            return

        # Show preview and ask for confirmation
        if not options['force']:
            self.show_preview(options)
            confirm = input('Are you sure you want to delete this data? (yes/no): ').lower()
            if confirm != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return

        # Execute the deletion
        if options['all']:
            self.clear_all_data(options)
        elif options['transactions']:
            self.clear_transactions(options)
        elif options['statements']:
            self.clear_statements(options)
        elif options['accounts']:
            self.clear_accounts(options)
        elif options['before']:
            self.clear_before_date(options)
        elif options['days']:
            self.clear_before_days(options)

    def show_preview(self, options):
        """Show what will be deleted"""
        self.stdout.write(self.style.WARNING('\n=== PREVIEW ==='))
        
        if options['all']:
            accounts = BankAccount.objects.all()
            statements = BankStatement.objects.all()
            transactions = Transaction.objects.all()
            
            self.stdout.write(f"Will delete:")
            self.stdout.write(f"  • {accounts.count()} accounts")
            self.stdout.write(f"  • {statements.count()} statements")
            self.stdout.write(f"  • {transactions.count()} transactions")
            
        elif options['transactions']:
            transactions = Transaction.objects.all()
            self.stdout.write(f"Will delete: {transactions.count()} transactions")
            
        elif options['statements']:
            statements = BankStatement.objects.all()
            self.stdout.write(f"Will delete: {statements.count()} statements")
            
        elif options['accounts']:
            accounts = BankAccount.objects.all()
            self.stdout.write(f"Will delete: {accounts.count()} accounts")
            
        elif options['before']:
            try:
                date = datetime.strptime(options['before'], '%Y-%m-%d').date()
                statements = BankStatement.objects.filter(upload_date__date__lt=date)
                transactions = Transaction.objects.filter(date__lt=date)
                
                self.stdout.write(f"Will delete data before {date}:")
                self.stdout.write(f"  • {statements.count()} statements")
                self.stdout.write(f"  • {transactions.count()} transactions")
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD'))
                return
                
        elif options['days']:
            days = options['days']
            cutoff_date = timezone.now() - timedelta(days=days)
            statements = BankStatement.objects.filter(upload_date__lt=cutoff_date)
            transactions = Transaction.objects.filter(created_at__lt=cutoff_date)
            
            self.stdout.write(f"Will delete data older than {days} days:")
            self.stdout.write(f"  • {statements.count()} statements")
            self.stdout.write(f"  • {transactions.count()} transactions")
        
        self.stdout.write('\n')

    def clear_all_data(self, options):
        """Clear all data"""
        try:
            # Delete in order to respect foreign keys
            transaction_count = Transaction.objects.all().count()
            statement_count = BankStatement.objects.all().count()
            account_count = BankAccount.objects.all().count()
            
            Transaction.objects.all().delete()
            BankStatement.objects.all().delete()
            BankAccount.objects.all().delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully cleared all data:\n'
                f'  • {transaction_count} transactions deleted\n'
                f'  • {statement_count} statements deleted\n'
                f'  • {account_count} accounts deleted'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError clearing data: {str(e)}'))

    def clear_transactions(self, options):
        """Clear transactions"""
        try:
            user_id = options.get('user')
            account_id = options.get('account')
            
            query = Transaction.objects.all()
            
            if account_id:
                query = query.filter(statement__account_id=account_id)
            elif user_id:
                query = query.filter(statement__account__user_id=user_id)
            
            count = query.count()
            query.delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully deleted {count} transactions'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError: {str(e)}'))

    def clear_statements(self, options):
        """Clear statements (and associated transactions)"""
        try:
            user_id = options.get('user')
            account_id = options.get('account')
            
            query = BankStatement.objects.all()
            
            if account_id:
                query = query.filter(account_id=account_id)
            elif user_id:
                query = query.filter(account__user_id=user_id)
            
            # Get transaction count before deletion
            transaction_count = Transaction.objects.filter(
                statement__in=query
            ).count()
            
            statement_count = query.count()
            query.delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully deleted:\n'
                f'  • {statement_count} statements\n'
                f'  • {transaction_count} associated transactions'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError: {str(e)}'))

    def clear_accounts(self, options):
        """Clear accounts (and associated statements & transactions)"""
        try:
            user_id = options.get('user')
            
            query = BankAccount.objects.all()
            
            if user_id:
                query = query.filter(user_id=user_id)
            
            # Get counts before deletion
            statement_count = BankStatement.objects.filter(
                account__in=query
            ).count()
            
            transaction_count = Transaction.objects.filter(
                statement__account__in=query
            ).count()
            
            account_count = query.count()
            query.delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully deleted:\n'
                f'  • {account_count} accounts\n'
                f'  • {statement_count} statements\n'
                f'  • {transaction_count} transactions'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError: {str(e)}'))

    def clear_before_date(self, options):
        """Clear data before specific date"""
        try:
            date = datetime.strptime(options['before'], '%Y-%m-%d').date()
            
            # Delete transactions
            transaction_count = Transaction.objects.filter(date__lt=date).count()
            Transaction.objects.filter(date__lt=date).delete()
            
            # Delete statements
            statement_count = BankStatement.objects.filter(
                upload_date__date__lt=date
            ).count()
            BankStatement.objects.filter(upload_date__date__lt=date).delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully deleted data before {date}:\n'
                f'  • {transaction_count} transactions\n'
                f'  • {statement_count} statements'
            ))
        except ValueError:
            self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError: {str(e)}'))

    def clear_before_days(self, options):
        """Clear data older than N days"""
        try:
            days = options['days']
            cutoff_date = timezone.now() - timedelta(days=days)
            
            # Delete transactions
            transaction_count = Transaction.objects.filter(
                created_at__lt=cutoff_date
            ).count()
            Transaction.objects.filter(created_at__lt=cutoff_date).delete()
            
            # Delete statements
            statement_count = BankStatement.objects.filter(
                upload_date__lt=cutoff_date
            ).count()
            BankStatement.objects.filter(upload_date__lt=cutoff_date).delete()
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Successfully deleted data older than {days} days:\n'
                f'  • {transaction_count} transactions\n'
                f'  • {statement_count} statements'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError: {str(e)}'))
