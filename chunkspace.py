import re

question = input("Ask Yourself!")
i = 0
X = []
print(question)

splited = re.split(r"\W+", question)
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

while True:
    save = input("Could you want to save it as file?(y/n)")

    if save in ['y', 'Y', 'n', 'N']:
        break
    else:
        print("Please try again.")

if save == 'y' or save == 'Y':
    print("1) .csv\n2) .dot\n3) both of them.")
    data = int(input("which?"))
    if data == 1:
        import csv
        edges = []
        for top_item in X:
            top_node = top_item[0]
            
            for mid_item in top_item[1:]:
                mid_node = mid_item[0]
                edge_label = f"{top_node}_{mid_node}"
                
                # 최상위 -> 중간 레벨
                edges.append((top_node, edge_label, mid_node))
                
                # 중간 레벨 -> 리프 노드
                for leaf in mid_item[1]:
                    leaf_label = f"{top_node}_{mid_node}_{leaf}"
                    edges.append((edge_label, leaf_label, leaf))
        
        with open('graph.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['from', 'to', 'label'])
            writer.writerows(edges)
        print("✓ graph.csv 파일 생성 완료!")
        
    elif data == 2:
        with open('graph.dot', 'w', encoding='utf-8') as f:
            f.write('digraph G {\n')
            f.write('  rankdir=LR;\n')
            f.write('  node [shape=box, fontname="Malgun Gothic"];\n\n')
            
            for top_item in X:
                top_node = top_item[0]
                
                for mid_item in top_item[1:]:
                    mid_node = mid_item[0]
                    edge_label = f"{top_node}_{mid_node}"
                    
                    f.write(f'  "{top_node}" -> "{edge_label}";\n')
                    f.write(f'  "{edge_label}" [label="{mid_node}"];\n')
                    
                    for leaf in mid_item[1]:
                        leaf_label = f"{top_node}_{mid_node}_{leaf}"
                        f.write(f'  "{edge_label}" -> "{leaf_label}";\n')
                        f.write(f'  "{leaf_label}" [label="{leaf}"];\n')
                    
                    f.write('\n')
            
            f.write('}\n')
        print("✓ graph.dot 파일 생성 완료!")
        print("\n[DOT 파일 사용법]")
        print("이미지 생성: dot -Tpng graph.dot -o output.png")
        print("또는:       dot -Tsvg graph.dot -o output.svg")
    elif data == 3:
        import csv
        edges = []
        for top_item in X:
            top_node = top_item[0]
            
            for mid_item in top_item[1:]:
                mid_node = mid_item[0]
                edge_label = f"{top_node}_{mid_node}"
                
                # 최상위 -> 중간 레벨
                edges.append((top_node, edge_label, mid_node))
                
                # 중간 레벨 -> 리프 노드
                for leaf in mid_item[1]:
                    leaf_label = f"{top_node}_{mid_node}_{leaf}"
                    edges.append((edge_label, leaf_label, leaf))
        
        with open('graph.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['from', 'to', 'label'])
            writer.writerows(edges)
        print("✓ graph.csv 파일 생성 완료!")
        
        with open('graph.dot', 'w', encoding='utf-8') as f:
            f.write('digraph G {\n')
            f.write('  rankdir=LR;\n')
            f.write('  node [shape=box, fontname="Malgun Gothic"];\n\n')
            
            for top_item in X:
                top_node = top_item[0]
                
                for mid_item in top_item[1:]:
                    mid_node = mid_item[0]
                    edge_label = f"{top_node}_{mid_node}"
                    
                    f.write(f'  "{top_node}" -> "{edge_label}";\n')
                    f.write(f'  "{edge_label}" [label="{mid_node}"];\n')
                    
                    for leaf in mid_item[1]:
                        leaf_label = f"{top_node}_{mid_node}_{leaf}"
                        f.write(f'  "{edge_label}" -> "{leaf_label}";\n')
                        f.write(f'  "{leaf_label}" [label="{leaf}"];\n')
                    
                    f.write('\n')
            
            f.write('}\n')
        print("✓ graph.dot 파일 생성 완료!")
        print("\n[DOT 파일 사용법]")
        print("이미지 생성: dot -Tpng graph.dot -o output.png")
        print("또는:       dot -Tsvg graph.dot -o output.svg")
    else:
        print("Wrong access. It will be broken.") 
            

    

    

