testdata = {
    "0": {
        "voteable": True,
        "1291333928493383701": {
            "usersvoted": [
                "771786441617047582 (ilikemice)"
            ]
        }
    },
    "1": {
        "voteable": True,
        "1326647895147155476": {
            "usersvoted": [
                "771786441617047582 (ilikemice)",
                "uhnsuhbihsb",
                "nijnizbizb"
            ]
        }
    }
}

uservotes = {}

for i in testdata["1"].items():
   if i[0] != "voteable":
      uservotes[i[0]] = len(i[1]["usersvoted"])
      print(uservotes)