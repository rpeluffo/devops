from securid import Token
from datetime import datetime
import xml.etree.ElementTree as ET
import base64

def load_token_from_sdtid(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Extract token info from XML
    tkn = root.find('TKN')
    header = root.find('TKNHeader')

    serial = tkn.find('SN').text.strip()

    seed_b64 = tkn.find('Seed').text.strip()
    seed = base64.b64decode(seed_b64)

    interval = int(header.find('DefInterval').text.strip())
    digits = int(header.find('DefDigits').text.strip())

    exp_date_str = header.find('DefDeath').text.strip()
    exp_date = datetime.strptime(exp_date_str, "%Y/%m/%d").date()

    # Create the Token instance
    token = Token(
        serial=serial,
        seed=seed,
        interval=interval,
        digits=digits,
        exp_date=exp_date
    )
    return token

# Path to your token file
token_file_path = r"C:\Users\rodri\Documents\_vscode\devops\devops\python_token\tokens\admin.stoken.sdtid"

token = load_token_from_sdtid(token_file_path)

# Generate OTP for current datetime
otp = token.generate_otp(datetime.now())
print(f"Token code: {otp}")
