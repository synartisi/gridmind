import re

question = input("Ask Yourself!")
i = 0
A = []
print(question)

splited = re.split(r"\W+", question)
old_spl = splited.copy()

print(splited)

while i < len(splited):
    new_A = []
    parent = splited[i]
    print(f"부모 = {parent}")
    splited.remove(parent)
    print(f"splited = {splited}")
    new_A.append(parent)
    for j in splited:
        notes = input("take your mind!")
        print(f"notes = {notes}")
        new_A.append([j, notes])
        print(f"기록 a = {new_A}")
    A.append(new_A)
    splited = old_spl.copy()
    i += 1

print(f"최종 : {A}")
