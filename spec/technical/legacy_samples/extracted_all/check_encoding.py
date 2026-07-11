import chardet
f = r'C:\projects\repos\RaoApp_new\spec\technical\legacy_samples\extracted_all\sections_extracted_v2.txt'
raw = open(f, 'rb').read(10000)
print(chardet.detect(raw))
