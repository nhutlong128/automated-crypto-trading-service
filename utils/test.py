import os

print("Started running bash file")
result = os.popen('bash utils/test.sh')
output = result.read()
print(output)
print("Finished")
