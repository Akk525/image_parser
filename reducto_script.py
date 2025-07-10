from pathlib import Path
from reducto_script import Reducto

client = Reducto()
upload = client.upload(file=Path("Invoice-4E62BC7A-0001.pdf"))
result = client.parse.run(document_url=upload)

print(result)