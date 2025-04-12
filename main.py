import requests
import time
import random
import json
import re
from datetime import datetime,timezone
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from fake_useragent import UserAgent
from colorama import Fore,init
from bs4 import BeautifulSoup
init(autoreset=True)
ua=UserAgent()
rpc_url='https://polygon-rpc.com'
chain_id=137
w3=Web3(Web3.HTTPProvider(rpc_url))
if w3.is_connected():print(Fore.GREEN+'✅ Successfully connected to ApeChain.')
else:print(Fore.RED+'❌ Failed to connect to ApeChain.')
def load_proxies(file_path='proxies.txt'):
	try:
		with open(file_path,'r')as file:proxies=[line.strip()for line in file if line.strip()]
		return proxies
	except FileNotFoundError:print(Fore.RED+f"❌ File '{file_path}' tidak ditemukan!");return[]
def get_proxy(proxies):
	if proxies:proxy=random.choice(proxies);return{'http':f"http://{proxy}",'https':f"http://{proxy}"}
	return None
def get_wallets_from_pk(file_path):
	try:
		with open(file_path,'r')as file:private_keys=[line.strip()for line in file if line.strip()]
		return[(Account.from_key(pk).address,pk)for pk in private_keys]
	except FileNotFoundError:print(Fore.RED+f"❌ File '{file_path}' tidak ditemukan!");exit()
def get_timestamp():return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]+'Z'
def get_nonce(proxies):
	url='https://evm-api.pulsar.money/auth/nonce';headers={'accept':'application/json','user-agent':ua.random}
	try:response=requests.get(url,headers=headers,proxies=proxies);response.raise_for_status();nonce=response.text.strip();set_cookie=response.headers.get('Set-Cookie','');connect_sid_match=re.search('connect\\.sid=([^;]+)',set_cookie);connect_sid=connect_sid_match.group(1)if connect_sid_match else None;timestamp=get_timestamp();return nonce,timestamp,connect_sid
	except requests.RequestException as e:print(Fore.RED+f"❌ Gagal mendapatkan nonce: {str(e)}");return None,None,None
def create_sign_message(address,nonce,timestamp):
	if not nonce or not timestamp:print(Fore.RED+'❌ Nonce atau timestamp tidak valid!');return None
	message=f"""app.pulsar.money wants you to sign in with your Ethereum account:
{address}

I Love Pulsar Money.

URI: https://app.pulsar.money
Version: 1
Chain ID: 8453
Nonce: {nonce}
Issued At: {timestamp}""";return message
def sign_message(private_key,message):
	try:message_encoded=encode_defunct(text=message);signed_message=Account.sign_message(message_encoded,private_key);return signed_message.signature.hex()
	except Exception as e:print(Fore.RED+f"❌ Error saat menandatangani pesan: {str(e)}");return None
def register_wallet(wallet_address,private_key,proxies):
	nonce,timestamp,connect_sid=get_nonce(proxies)
	if not nonce or not connect_sid:print(Fore.RED+f"[{wallet_address}] Gagal mendapatkan nonce atau connect.sid!");return None
	message=create_sign_message(wallet_address,nonce,timestamp)
	if not message:return None
	signature=sign_message(private_key,message)
	if not signature:return None
	headers={'accept':'application/json','content-type':'application/json','cookie':f"connect.sid={connect_sid}",'user-agent':ua.random};payload={'message':message,'signature':'0x'+signature};url='https://evm-api.pulsar.money/auth/verify'
	try:response=requests.post(url,headers=headers,json=payload,proxies=proxies,timeout=10);response.raise_for_status();print(Fore.GREEN+f"[{wallet_address}] ✅ login sukses!");return connect_sid
	except requests.RequestException as e:print(Fore.RED+f"[{wallet_address}] ❌ Gagal login: {str(e)}");return None
def send_verif_mail(account_address,connect_sid,proxies):
	proxy=get_proxy(proxies);url='https://evm-api.pulsar.money/users/link-email';headers={'accept':'application/json, text/plain, */*','accept-language':'en-US,en;q=0.9','content-type':'application/json','cookie':f"connect.sid={connect_sid}",'origin':'https://app.pulsar.money','priority':'u=1, i','referer':'https://app.pulsar.money/','sec-ch-ua':'"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"','sec-ch-ua-mobile':'?1','sec-ch-ua-platform':'"Android"','sec-fetch-dest':'empty','sec-fetch-mode':'cors','sec-fetch-site':'same-site','user-agent':ua.random};payload={'email':f"{account_address}@dmail.ai"};short_address=f"{account_address[:6]}...{account_address[-4:]}";masked_email=f"{short_address}@multiversex@mail.ai"
	try:
		response=requests.post(url,headers=headers,json=payload,proxies=proxy,timeout=10)
		if response.status_code==201:print(f"[+] Verification email sent to {masked_email}")
		else:print(f"[-] Failed to send verification to {short_address} | Status: {response.status_code} | Response: {response.text}")
	except requests.exceptions.RequestException as e:print(f"[!] Error sending verification to {short_address}: {e}")
def mail(private_key):
	verification_code=None
	try:
		account=Account.from_key(private_key);address=account.address;print(f"🟢 Wallet: {address}");nonce_res=requests.get('https://icp.dmail.ai/api/node/v6/dmail/auth/generate_nonce')
		if nonce_res.status_code!=200:print('❌ Gagal mendapatkan nonce!');return None
		nonce=nonce_res.json().get('data',{}).get('nonce');current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S');message=f"""SIGN THIS MESSAGE TO LOGIN TO THE INTERNET COMPUTER

APP NAME: 
dmail

ADDRESS: 
{address}

NONCE: 
{nonce}

CURRENT TIME: 
{current_time}""";signed_message=w3.eth.account.sign_message(encode_defunct(text=message),private_key);signature=signed_message.signature.hex();print(f"🔑 Signature: {signature[:10]}...");login_data={'message':{'Message':'SIGN THIS MESSAGE TO LOGIN TO THE INTERNET COMPUTER','APP NAME':'dmail','ADDRESS':address,'NONCE':nonce,'CURRENT TIME':current_time},'signature':'0x'+signature,'wallet_name':'metamask','chain_id':8453};login_res=requests.post('https://icp.dmail.ai/api/node/v6/dmail/auth/evm_verify_signature',headers={'accept':'application/json','content-type':'application/json'},json=login_data)
		if login_res.status_code!=200 or not login_res.json().get('success'):print(f"❌ Login Gagal untuk {address}");return None
		data=login_res.json().get('data',{});token,pid=data.get('token'),data.get('pid');print(f"✅ Login email sukses! Token: {token[:10]}... PID: {pid}");inbox_res=requests.post('https://icp.dmail.ai/api/node/v6/dmail/inbox_all/read_by_page_with_content',headers={'accept':'application/json','content-type':'application/json','dm-encstring':token,'dm-pid':pid},json={'dm_folder':'inbox','store_type':'mail','pageInfo':{'page':1,'pageSize':1}})
		if inbox_res.status_code!=200:print('📭 Tidak ada email masuk.');return None
		email_list=inbox_res.json().get('data',{}).get('list',[])
		for email in email_list:
			if email.get('dm_salias')=='contact@pulsar.money':
				soup=BeautifulSoup(email.get('content',{}).get('html',''),'html.parser');match=re.search('\\b[a-fA-F0-9]{6}\\b',soup.get_text())
				if match:verification_code=match.group(0);print(f"🔑 Verification Code: {verification_code}");break
		time.sleep(2)
	except Exception as e:print(f"⚠️ Error: {e}")
	return verification_code
def verify_email(verification_code,connect_sid,proxies):
	proxy=get_proxy(proxies);url='https://evm-api.pulsar.money/users/verify-email';headers={'accept':'application/json, text/plain, */*','content-type':'application/json','cookie':f"connect.sid={connect_sid}",'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Mobile Safari/537.36','origin':'https://app.pulsar.money','referer':'https://app.pulsar.money/'};payload={'code':verification_code}
	try:
		response=requests.post(url,headers=headers,json=payload,proxies=proxy,timeout=10)
		if response.status_code==201:print(f"[+] Email verified with code {verification_code}")
		else:print(f"[-] Failed to verify email | Status: {response.status_code} | Response: {response.text}")
	except requests.exceptions.RequestException as e:print(f"[!] Error during email verification: {e}")
file_path='pk-film3.txt'
if __name__=='__main__':
	while True:
		start_time=datetime.now();print(Fore.MAGENTA+f"\n🚀 Mulai proses pada {start_time.strftime("%Y-%m-%d %H:%M:%S")}");proxies=load_proxies('proxies.txt');wallets=get_wallets_from_pk(file_path)
		for(account_address,private_key)in wallets:
			print(Fore.YELLOW+f"\n📲 Proses wallet: {account_address} pakai proxy: {get_proxy(proxies)}");proxy=get_proxy(proxies);connect_sid=register_wallet(account_address,private_key,proxy)
			if connect_sid:print(Fore.CYAN+f"[{account_address}] 🔥 Melakukan verify email task");send_verif_mail(account_address,connect_sid,proxies);time.sleep(40);verification_code=mail(private_key);verify_email(verification_code,connect_sid,proxies)
			sleep_time=random.randint(10,15);print(Fore.GREEN+f"⏳ Sleeping for {sleep_time} seconds...");time.sleep(sleep_time)
		print(Fore.BLUE+'\n⏳ Semua akun selesai. Menunggu 24 jam sebelum menjalankan ulang...\n');time.sleep(86400)
