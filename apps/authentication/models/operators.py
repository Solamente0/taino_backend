# class Operator(BaseModel):
#     users = models.ManyToManyField(to="TainoUser", verbose_name=_("operator users"))
#     department = models.ForeignKey(
#         to="departments.Department", on_delete=models.CASCADE, related_name="operators", verbose_name=_("department")
#     )
#     wallet = models.ForeignKey(
#         to="wallet.MainWallet", on_delete=models.CASCADE, related_name="wallets", verbose_name=_("wallet")
#     )
#     has_super_access = models.BooleanField(_("has super-access"))
#
#     def get_operators_vekalat_id(self):
#         return self.users.values_list("vekalat_id", flat=True)
#
#     def get_operators_id(self):
#         return self.users.values_list("id", flat=True)
#
#     class Meta:
#         verbose_name = _("Operator")
#         verbose_name_plural = _("Operators")
