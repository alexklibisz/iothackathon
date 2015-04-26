import json
data = "test"
with open('data.txt', 'w') as outfile:
    json.dump(data, outfile)
