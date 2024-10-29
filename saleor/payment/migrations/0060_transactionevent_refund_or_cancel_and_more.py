# Generated by Django 4.2.15 on 2024-10-29 10:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0059_merge_20240802_1125"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transactionevent",
            name="type",
            field=models.CharField(
                choices=[
                    ("authorization_success", "Represents success authorization"),
                    ("authorization_failure", "Represents failure authorization"),
                    ("authorization_adjustment", "Represents authorization adjustment"),
                    ("authorization_request", "Represents authorization request"),
                    (
                        "authorization_action_required",
                        "Represents additional actions required for authorization.",
                    ),
                    (
                        "charge_action_required",
                        "Represents additional actions required for charge.",
                    ),
                    ("charge_success", "Represents success charge"),
                    ("charge_failure", "Represents failure charge"),
                    ("charge_back", "Represents chargeback."),
                    ("charge_request", "Represents charge request"),
                    ("refund_success", "Represents success refund"),
                    ("refund_failure", "Represents failure refund"),
                    ("refund_reverse", "Represents reverse refund"),
                    ("refund_request", "Represents refund request"),
                    ("cancel_success", "Represents success cancel"),
                    ("cancel_failure", "Represents failure cancel"),
                    ("cancel_request", "Represents cancel request"),
                    ("info", "Represents an info event"),
                    ("refund_or_cancel_request", "Represents refund or cancel request"),
                    ("refund_or_cancel_success", "Represents refund or cancel success"),
                    ("refund_or_cancel_failure", "Represents refund or cancel failure"),
                ],
                default="info",
                max_length=128,
            ),
        ),
        migrations.AddField(
            model_name="transactionevent",
            name="refund_or_cancel",
            field=models.BooleanField(default=False),
        ),
        migrations.RunSQL(
            """
                ALTER TABLE payment_transactionevent
                ALTER COLUMN refund_or_cancel
                SET DEFAULT false;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
