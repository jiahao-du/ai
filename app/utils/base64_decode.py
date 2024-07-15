def decode_env(file_path='.env.b64'):
    import base64
    with open(file_path, 'r') as file:
        encoded_str = file.read()
    encoded_str = encoded_str.replace("-----BEGIN CERTIFICATE-----", "").replace("-----END CERTIFICATE-----", "")
    if len(encoded_str) % 4 != 0:
        # 计算需要填充的等号数量
        padding = 4 - (len(encoded_str) % 4)
        # 填充等号
        encoded_str += "=" * padding

    decoded_bytes = base64.b64decode(encoded_str)
    decoded_str = decoded_bytes.decode('utf-8', errors='replace')
    data = {}
    for line in decoded_str.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            data[key] = value
    return data
