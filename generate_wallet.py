from eth_account import Account
import secrets

# Generate a fresh Polygon wallet
private_key = "0x" + secrets.token_hex(32)
account = Account.from_key(private_key)

print("=" * 60)
print("NEW WALLET GENERATED")
print("=" * 60)
print(f"Wallet Address : {account.address}")
print(f"Private Key    : {private_key}")
print("=" * 60)
print("IMPORTANT:")
print("1. Copy these values into your .env file NOW")
print("2. Never share your private key with anyone")
print("3. Delete this output from your terminal after copying")
print("=" * 60)
