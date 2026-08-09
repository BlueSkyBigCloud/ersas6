from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_customuser_is_account_admin"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE users_customuser DROP COLUMN subscription_paid;",
            reverse_sql="ALTER TABLE users_customuser ADD COLUMN subscription_paid boolean NOT NULL DEFAULT false;",
        ),
    ]