"""
Management command to populate global rules for transaction categorization.

This command creates a comprehensive set of default rules that can be copied
to user accounts for automatic transaction categorization.

Usage:
    python manage.py populate_global_rules
    python manage.py populate_global_rules --user <username>
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from analyzer.models import Rule, RuleCondition


class Command(BaseCommand):
    help = 'Populate global default rules for transaction categorization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Apply rules to specific user (username)',
        )

    def handle(self, *args, **options):
        target_user = None
        
        # Get target user if specified
        if options['user']:
            try:
                target_user = User.objects.get(username=options['user'])
                self.stdout.write(f"Creating rules for user: {target_user.username}")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User '{options['user']}' not found"))
                return

        # Define global rules
        rules_data = [
            # FOOD & DINING
            {
                'name': 'Restaurants & Cafes',
                'category': 'FOOD',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'restaurant', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'cafe', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'pizza', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'burger', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Food Delivery Apps',
                'category': 'FOOD',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'zomato', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'swiggy', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'ubereats', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'foodpanda', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Grocery & Supermarket',
                'category': 'FOOD',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'grocery', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'supermarket', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'blinkit', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'bigbasket', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'reliance fresh', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },

            # SHOPPING
            {
                'name': 'Online Shopping Platforms',
                'category': 'SHOPPING',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'amazon', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'flipkart', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'myntra', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'ebay', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Clothing & Fashion',
                'category': 'SHOPPING',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'fashion', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'apparel', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'clothing', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'store', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Department Stores',
                'category': 'SHOPPING',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'mall', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'retail', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'shop', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },

            # TRANSPORTATION
            {
                'name': 'Ride Sharing Services',
                'category': 'TRANSPORT',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'uber', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'ola', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'lyft', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'bolt', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Fuel & Petrol',
                'category': 'TRANSPORT',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'petrol', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'fuel', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'gas', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'shell', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'iocl', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Public Transport & Metro',
                'category': 'TRANSPORT',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'metro', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'railway', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'bus', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'train', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },

            # ENTERTAINMENT
            {
                'name': 'Streaming & Movies',
                'category': 'ENTERTAINMENT',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'netflix', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'prime video', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'hotstar', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'cinema', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'movie', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Gaming & Entertainment',
                'category': 'ENTERTAINMENT',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'game', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'spotify', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'music', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'gaming', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },

            # HEALTHCARE & MEDICAL
            {
                'name': 'Medical & Pharmacy',
                'category': 'HEALTHCARE',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'pharmacy', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'medicine', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'medical', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': '1mg', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'netmeds', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Doctors & Healthcare',
                'category': 'HEALTHCARE',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'doctor', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'hospital', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'clinic', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'health', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },

            # TRAVEL & ACCOMMODATION
            {
                'name': 'Flight Bookings',
                'category': 'TRAVEL',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'flight', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'airline', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'skyscanner', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'makemytrip', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Hotel & Accommodation',
                'category': 'TRAVEL',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'hotel', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'booking', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'airbnb', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'resort', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },

            # BILLS & UTILITIES
            {
                'name': 'Electricity & Utilities',
                'category': 'BILLS',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'electricity', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'electric', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'power', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'utility', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Internet & Mobile Bills',
                'category': 'BILLS',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'airtel', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'jio', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'vodafone', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'internet', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'broadband', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
            {
                'name': 'Insurance & Subscriptions',
                'category': 'BILLS',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'insurance', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'subscription', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'premium', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },

            # LOANS & EMI
            {
                'name': 'Loan Payments & EMI',
                'category': 'LOAN',
                'conditions': [
                    {'type': 'KEYWORD', 'keyword': 'loan', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'emi', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'installment', 'match': 'CONTAINS'},
                    {'type': 'KEYWORD', 'keyword': 'credit', 'match': 'CONTAINS'},
                ],
                'rule_type': 'OR',
            },
        ]

        # Create rules for specified user or create as default system rules
        if target_user:
            self.create_rules_for_user(target_user, rules_data)
        else:
            self.stdout.write("Creating system default rules (not assigned to specific user):")
            self.stdout.write(self.style.WARNING("Note: To apply rules to users, use --user flag"))
            self.create_rules_for_user(None, rules_data)

    def create_rules_for_user(self, user, rules_data):
        """Create rules for a specific user"""
        created_count = 0
        skipped_count = 0

        for rule_data in rules_data:
            # Check if rule already exists for this user
            if user:
                rule_exists = Rule.objects.filter(
                    user=user,
                    name=rule_data['name']
                ).exists()

                if rule_exists:
                    skipped_count += 1
                    self.stdout.write(f"  ⊘ Skipped: {rule_data['name']} (already exists)")
                    continue

                # Create rule for user
                rule = Rule.objects.create(
                    user=user,
                    name=rule_data['name'],
                    category=rule_data['category'],
                    rule_type=rule_data['rule_type'],
                    is_active=True
                )
            else:
                # Check if rule exists at system level
                rule_exists = Rule.objects.filter(
                    name=rule_data['name'],
                    user__isnull=True
                ).exists()

                if rule_exists:
                    skipped_count += 1
                    self.stdout.write(f"  ⊘ Skipped: {rule_data['name']} (already exists)")
                    continue

                # For demo purposes, create for first user or skip
                if not user:
                    # Get first user as demo
                    try:
                        user = User.objects.first()
                        if not user:
                            self.stdout.write(self.style.WARNING("No users found. Create a user first."))
                            return
                    except:
                        self.stdout.write(self.style.WARNING("Error retrieving user."))
                        return

                rule = Rule.objects.create(
                    user=user,
                    name=rule_data['name'],
                    category=rule_data['category'],
                    rule_type=rule_data['rule_type'],
                    is_active=True
                )

            # Create conditions for rule
            for condition_data in rule_data['conditions']:
                if condition_data['type'] == 'KEYWORD':
                    RuleCondition.objects.create(
                        rule=rule,
                        condition_type='KEYWORD',
                        keyword=condition_data['keyword'],
                        keyword_match_type=condition_data['match']
                    )

            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f"  ✓ Created: {rule_data['name']} ({len(rule_data['conditions'])} conditions)")
            )

        # Print summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"Successfully created: {created_count} rules"))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f"Skipped: {skipped_count} rules (already exist)"))
        self.stdout.write("="*60)
