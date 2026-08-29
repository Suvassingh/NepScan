import uuid
from django.db import models
from common.fields import EncryptedTextField, DecryptOnAccessMixin


class ExpenseData(DecryptOnAccessMixin, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_id = models.UUIDField(unique=True, db_index=True)
    vendor_encrypted = EncryptedTextField(db_column='vendor', aad_field='document_id')
    expense_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=50, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='NPR')

    class Meta:
        db_table = 'expense_data'
        managed = False  # table is owned by Supabase / mirrored in apps.supabase_models.ExpenseData

    @property
    def vendor(self):
        return self._decrypt_field('vendor_encrypted', 'document_id')

    @vendor.setter
    def vendor(self, value):
        self.vendor_encrypted = value