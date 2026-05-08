resource "random_password" "secret_key" {
  length           = 48
  special          = true
  override_special = "!#%()*+,-.:?^_~"
}
