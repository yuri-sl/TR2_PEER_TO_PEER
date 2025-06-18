import hashlib

def calcular_checksum(texto):
    return hashlib.sha256(texto.encode('utf-8')).hexdigest()

texto_original = "Alguma coisa deve ser dividida em Chunks agora"
texto_bytes = texto_original.encode('utf-8')

checksum_original = calcular_checksum(texto_original)

checksum_bytes = calcular_checksum(texto_bytes)

print("Texto original:", texto_original)
print("Bytes:", texto_bytes)
print("Checksum original:", checksum_original)
print(checksum_bytes)
