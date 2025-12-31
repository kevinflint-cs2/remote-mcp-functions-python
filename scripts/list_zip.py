import zipfile
zf = zipfile.ZipFile('released-package.zip')
for i,name in enumerate(zf.namelist()):
    print(name)
print('\nTotal entries:', len(zf.namelist()))
