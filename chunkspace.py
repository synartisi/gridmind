import re

question = input("Ask Yourself!")
i = 0
X = []
print(question)

splited = re.split(r"\W+", question)
if splited:  # 수정이 필요한 부분
    for k in splited:
        print(k)
        idx = splited.index(k)
        print(idx)
        check = input("Is it OK?")
        if check == "X" or check == "x":
            if idx == 0:
                splited.remove(k)
                continue
            splited[idx - 1] += splited[idx]
            splited.remove(k)
            print(splited)
            print("It was removed!")  # 수정이 필요한 부분

print(splited)
const_spl = splited.copy()

while i < len(splited):
    Y = []
    parent = splited[i]
    print(f"부모 = {parent}")
    splited.remove(parent)
    print(f"splited = {splited}")
    Y.append(parent)
    for j in splited:
        notes = input("take your mind!")
        print(f"notes = {notes}")
        Z = re.split(r"\W+", notes)
        Y.append([j, Z])
        print(f"기록 a = {Y}")
    X.append(Y)
    splited = const_spl.copy()
    i += 1

print(f"최종 : {X}")
