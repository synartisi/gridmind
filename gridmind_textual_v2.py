#!/usr/bin/env python3
"""
Mind Mapper TUI v2 - 원문 보존 + 향상된 시각화
"""
import re
import csv
import json
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Tree, Input, Button, 
    Static, Label, TextArea, DataTable
)
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.binding import Binding
from textual.reactive import reactive


class MindMapApp(App):
    """마인드맵 TUI 애플리케이션 v2"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        layout: horizontal;
        height: 100%;
    }
    
    #left-panel {
        width: 35%;
        border: solid $primary;
        padding: 1;
    }
    
    #right-panel {
        width: 65%;
        border: solid $accent;
        padding: 1;
    }
    
    #tree-container {
        height: 1fr;
        border: solid $success;
        padding: 1;
        margin-top: 1;
    }
    
    #history-container {
        height: 15;
        border: solid $warning;
        padding: 1;
        margin-top: 1;
    }
    
    #input-area {
        height: auto;
        border: solid $warning;
        padding: 1;
        margin-top: 1;
    }
    
    #status-area {
        height: auto;
        background: $boost;
        padding: 1;
        margin-top: 1;
    }
    
    #controls {
        layout: horizontal;
        height: auto;
        padding: 1;
        background: $panel;
    }
    
    Tree {
        height: 100%;
    }
    
    DataTable {
        height: 100%;
    }
    
    Input {
        margin: 1 0;
    }
    
    TextArea {
        height: 5;
        margin: 1 0;
    }
    
    Button {
        margin: 0 1;
    }
    
    .title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    .highlight {
        background: $primary-darken-1;
        padding: 0 1;
    }
    
    .success-msg {
        color: $success;
        text-style: bold;
    }
    
    .warning-msg {
        color: $warning;
        text-style: bold;
    }
    
    .thought-preview {
        color: $text-muted;
        text-style: italic;
        margin: 0 2;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+s", "save_graph", "Save", show=True),
        Binding("ctrl+r", "reset", "Reset", show=True),
        Binding("ctrl+h", "toggle_history", "History", show=True),
    ]
    
    # 상태 관리
    current_phase = reactive("init")
    current_index = reactive(0)
    current_parent = reactive("")
    show_history = reactive(True)
    
    def __init__(self):
        super().__init__()
        self.X = []
        self.question = ""
        self.question_words = []
        self.const_spl = []
        self.current_Y = []
        self.current_child_index = 0
        self.remaining_children = []
        self.connection_history = []  # 입력 이력
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        yield Header()
        
        with Container(id="main-container"):
            # 왼쪽 패널 - 트리 시각화 + 히스토리
            with Vertical(id="left-panel"):
                yield Static("🧠 Mind Structure", classes="title")
                with ScrollableContainer(id="tree-container"):
                    yield Tree("Mindmap", id="mindmap-tree")
                
                yield Static("📝 Connection History", classes="title", id="history-title")
                with ScrollableContainer(id="history-container"):
                    table = DataTable(id="history-table")
                    table.add_columns("From", "To", "Thought")
                    yield table
            
            # 오른쪽 패널 - 입력 영역
            with Vertical(id="right-panel"):
                yield Static("💡 Input Area", classes="title")
                
                # 상태 표시
                with Container(id="status-area"):
                    yield Label("시작하려면 질문을 입력하세요", id="status-label")
                    yield Label("", id="progress-label")
                
                # 입력 영역
                with Container(id="input-area"):
                    yield Label("Question:", id="input-title")
                    yield Input(
                        placeholder="질문 입력 (예: 효율적인 시스템이란?)",
                        id="question-input"
                    )
                    
                    yield Label("", id="relation-label")
                    
                    yield Label("Your Thought (원문이 저장됩니다):", id="thought-label")
                    yield TextArea(
                        id="notes-textarea",
                        disabled=True
                    )
                    
                    yield Label("💡 Tip: 생각을 자유롭게 쓰세요. 단어만 추출됩니다.", 
                               classes="thought-preview")
        
        # 하단 컨트롤
        with Horizontal(id="controls"):
            yield Button("Start", id="start-btn", variant="success")
            yield Button("Next →", id="next-btn", variant="primary", disabled=True)
            yield Button("Skip", id="skip-btn", variant="default", disabled=True)
            yield Button("Undo", id="undo-btn", variant="default", disabled=True)
            yield Button("Save", id="save-btn", variant="warning", disabled=True)
            yield Button("Reset", id="reset-btn", variant="error")
        
        yield Footer()
    
    def on_mount(self):
        """앱 시작 시"""
        self.query_one("#question-input").focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """버튼 클릭 처리"""
        button_id = event.button.id
        
        if button_id == "start-btn":
            self.start_mapping()
        elif button_id == "next-btn":
            self.process_current()
        elif button_id == "skip-btn":
            self.skip_current()
        elif button_id == "undo-btn":
            self.undo_last()
        elif button_id == "save-btn":
            self.action_save_graph()
        elif button_id == "reset-btn":
            self.action_reset()
    
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """TextArea에서 Ctrl+Enter 감지"""
        if event.text_area.id == "notes-textarea":
            # Ctrl+Enter로 제출 (실제로는 버튼 클릭 권장)
            pass
    
    def start_mapping(self):
        """매핑 시작"""
        question_input = self.query_one("#question-input", Input)
        self.question = question_input.value.strip()
        
        if not self.question:
            self.update_status("❌ 질문을 입력하세요!", "warning")
            return
        
        # 질문 파싱
        self.question_words = [s for s in re.split(r"\W+", self.question) if s]
        
        if len(self.question_words) < 2:
            self.update_status("❌ 최소 2개 이상의 단어가 필요합니다!", "warning")
            return
        
        self.const_spl = self.question_words.copy()
        self.current_phase = "collecting"
        self.current_index = 0
        
        # UI 상태 업데이트
        question_input.disabled = True
        self.query_one("#start-btn").disabled = True
        self.query_one("#next-btn").disabled = False
        self.query_one("#skip-btn").disabled = False
        self.query_one("#undo-btn").disabled = False
        self.query_one("#notes-textarea").disabled = False
        
        # 첫 단계 시작
        self.start_next_parent()
    
    def start_next_parent(self):
        """다음 부모 노드 처리 시작"""
        if self.current_index >= len(self.const_spl):
            self.complete_mapping()
            return
        
        self.current_parent = self.const_spl[self.current_index]
        self.current_Y = [self.current_parent]
        self.remaining_children = [w for w in self.const_spl if w != self.current_parent]
        self.current_child_index = 0
        
        self.prompt_next_relation()
    
    def prompt_next_relation(self):
        """다음 관계 입력 프롬프트"""
        if self.current_child_index >= len(self.remaining_children):
            # 현재 부모 노드 완료
            self.X.append(self.current_Y)
            self.update_tree()
            self.current_index += 1
            self.start_next_parent()
            return
        
        current_child = self.remaining_children[self.current_child_index]
        
        # 상태 업데이트
        progress = f"[{self.current_index + 1}/{len(self.const_spl)}] 부모: {self.current_parent}"
        self.query_one("#progress-label").update(progress)
        
        relation_text = f"💭 '{self.current_parent}' ↔ '{current_child}' 의 관계를 설명하세요:"
        self.query_one("#relation-label").update(relation_text)
        
        self.update_status(
            f"진행 중... ({self.current_child_index + 1}/{len(self.remaining_children)} 관계)",
            "success"
        )
        
        # TextArea 클리어 및 포커스
        text_area = self.query_one("#notes-textarea", TextArea)
        text_area.clear()
        text_area.focus()
    
    def process_current(self):
        """현재 입력 처리"""
        text_area = self.query_one("#notes-textarea", TextArea)
        notes = text_area.text.strip()
        
        if notes:
            current_child = self.remaining_children[self.current_child_index]
            Z = [s for s in re.split(r"\W+", notes) if s]
            
            # ✅ 원문 보존
            connection = {
                'child': current_child,
                'raw_thought': notes,  # 원문
                'keywords': Z
            }
            
            self.current_Y.append(connection)
            
            # 히스토리에 추가
            self.connection_history.append({
                'from': self.current_parent,
                'to': current_child,
                'thought': notes,
                'keywords': Z
            })
            
            # 히스토리 테이블 업데이트
            self.update_history_table()
            
            self.notify(f"✓ 기록됨: {self.current_parent} → {current_child}")
        
        self.current_child_index += 1
        self.prompt_next_relation()
    
    def skip_current(self):
        """현재 관계 건너뛰기"""
        current_child = self.remaining_children[self.current_child_index]
        
        connection = {
            'child': current_child,
            'raw_thought': '',
            'keywords': []
        }
        
        self.current_Y.append(connection)
        self.notify(f"⊘ 건너뜀: {self.current_parent} → {current_child}")
        
        self.current_child_index += 1
        self.prompt_next_relation()
    
    def undo_last(self):
        """마지막 입력 되돌리기"""
        if self.connection_history:
            last = self.connection_history.pop()
            
            # current_Y에서도 제거
            if len(self.current_Y) > 1:
                self.current_Y.pop()
            
            self.update_history_table()
            self.notify(f"↶ 되돌림: {last['from']} → {last['to']}")
            
            # 이전 단계로
            if self.current_child_index > 0:
                self.current_child_index -= 1
                self.prompt_next_relation()
    
    def complete_mapping(self):
        """매핑 완료"""
        self.current_phase = "complete"
        
        self.query_one("#notes-textarea").disabled = True
        self.query_one("#next-btn").disabled = True
        self.query_one("#skip-btn").disabled = True
        self.query_one("#undo-btn").disabled = True
        self.query_one("#save-btn").disabled = False
        
        self.update_status("✨ 완성! 저장할 수 있습니다.", "success")
        self.query_one("#progress-label").update("")
        self.query_one("#relation-label").update("")
        
        self.update_tree()
        self.notify("🎉 마인드맵 생성 완료!")
    
    def update_tree(self):
        """트리 UI 업데이트 - 원문 프리뷰 포함"""
        tree = self.query_one("#mindmap-tree", Tree)
        tree.clear()
        
        root = tree.root
        root.expand()
        
        for top_item in self.X:
            if not top_item:
                continue
                
            top_node = top_item[0]
            top_branch = root.add(f"🔵 {top_node}", expand=True)
            
            for connection in top_item[1:]:
                if not isinstance(connection, dict):
                    continue
                
                child = connection['child']
                thought = connection['raw_thought']
                keywords = connection['keywords']
                
                # 생각 프리뷰 (첫 30자)
                preview = thought[:30] + "..." if len(thought) > 30 else thought
                
                if thought:
                    # 생각이 있으면 상세 표시
                    mid_branch = top_branch.add(f"🟡 {child}", expand=False)
                    mid_branch.add_leaf(f"💭 {preview}")
                    
                    # 키워드들
                    if keywords:
                        kw_branch = mid_branch.add(f"🔑 Keywords", expand=False)
                        for kw in keywords[:5]:  # 최대 5개만
                            kw_branch.add_leaf(f"🟢 {kw}")
                else:
                    # 생각 없음 (스킵)
                    top_branch.add_leaf(f"⊘ {child}")
    
    def update_history_table(self):
        """히스토리 테이블 업데이트"""
        table = self.query_one("#history-table", DataTable)
        table.clear()
        
        for item in self.connection_history[-10:]:  # 최근 10개만
            thought_preview = item['thought'][:40] + "..." if len(item['thought']) > 40 else item['thought']
            table.add_row(
                item['from'],
                item['to'],
                thought_preview
            )
    
    def update_status(self, message: str, style: str = ""):
        """상태 메시지 업데이트"""
        label = self.query_one("#status-label", Label)
        
        if style == "success":
            label.update(f"[green]{message}[/]")
        elif style == "warning":
            label.update(f"[yellow]{message}[/]")
        elif style == "error":
            label.update(f"[red]{message}[/]")
        else:
            label.update(message)
    
    def action_save_graph(self):
        """그래프 저장 - 원문 포함"""
        if not self.X:
            self.notify("저장할 데이터가 없습니다!", severity="warning")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV 저장 (원문 포함)
        csv_filename = f"mindmap_{timestamp}.csv"
        self.save_csv_with_thoughts(csv_filename)
        
        # JSON 저장 (완전한 구조)
        json_filename = f"mindmap_{timestamp}.json"
        self.save_json(json_filename)
        
        # DOT 저장 (시각화용)
        dot_filename = f"mindmap_{timestamp}.dot"
        self.save_dot_with_thoughts(dot_filename)
        
        self.notify(f"💾 저장 완료!\n{csv_filename}\n{json_filename}\n{dot_filename}", 
                   severity="information")
        self.update_status(f"✓ 파일 저장됨", "success")
    
    def save_csv_with_thoughts(self, filename: str):
        """CSV 파일로 저장 - 원문 포함"""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['from', 'to', 'label', 'thought', 'keywords'])
            
            for top_item in self.X:
                top_node = top_item[0]
                
                for connection in top_item[1:]:
                    if not isinstance(connection, dict):
                        continue
                    
                    child = connection['child']
                    thought = connection['raw_thought']
                    keywords = ', '.join(connection['keywords'][:5])
                    
                    writer.writerow([
                        top_node,
                        child,
                        child,
                        thought,
                        keywords
                    ])
    
    def save_json(self, filename: str):
        """JSON 파일로 저장 - 완전한 구조"""
        data = {
            'version': '2.0',
            'question': self.question,
            'timestamp': datetime.now().isoformat(),
            'structure': self.X,
            'connection_history': self.connection_history
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_dot_with_thoughts(self, filename: str):
        """DOT 파일로 저장 - 툴팁에 원문 포함"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('digraph G {\n')
            f.write('  rankdir=LR;\n')
            f.write('  node [shape=box, fontname="Malgun Gothic"];\n\n')
            
            for top_item in self.X:
                top_node = top_item[0]
                
                for connection in top_item[1:]:
                    if not isinstance(connection, dict):
                        continue
                    
                    child = connection['child']
                    thought = connection['raw_thought'].replace('"', '\\"')
                    
                    edge_label = f"{top_node}_{child}"
                    
                    # 노드 연결 (툴팁에 원문)
                    f.write(f'  "{top_node}" -> "{child}" [\n')
                    f.write(f'    label="",\n')
                    if thought:
                        f.write(f'    tooltip="{thought}",\n')
                    f.write(f'  ];\n')
                    
                    # 키워드 노드들
                    for kw in connection['keywords'][:3]:
                        f.write(f'  "{child}" -> "{kw}" [style=dashed];\n')
                    
                    f.write('\n')
            
            f.write('}\n')
    
    def action_reset(self):
        """초기화"""
        self.X = []
        self.question = ""
        self.question_words = []
        self.const_spl = []
        self.current_Y = []
        self.current_index = 0
        self.current_child_index = 0
        self.remaining_children = []
        self.current_phase = "init"
        self.connection_history = []
        
        # UI 초기화
        self.query_one("#question-input", Input).value = ""
        self.query_one("#question-input").disabled = False
        self.query_one("#notes-textarea", TextArea).clear()
        self.query_one("#notes-textarea").disabled = True
        
        self.query_one("#start-btn").disabled = False
        self.query_one("#next-btn").disabled = True
        self.query_one("#skip-btn").disabled = True
        self.query_one("#undo-btn").disabled = True
        self.query_one("#save-btn").disabled = True
        
        self.query_one("#status-label").update("시작하려면 질문을 입력하세요")
        self.query_one("#progress-label").update("")
        self.query_one("#relation-label").update("")
        
        # 트리 초기화
        tree = self.query_one("#mindmap-tree", Tree)
        tree.clear()
        tree.root.set_label("Mindmap")
        
        # 히스토리 테이블 초기화
        table = self.query_one("#history-table", DataTable)
        table.clear()
        
        self.query_one("#question-input").focus()
        self.notify("🔄 초기화 완료")
    
    def action_toggle_history(self):
        """히스토리 패널 토글"""
        history_container = self.query_one("#history-container")
        history_title = self.query_one("#history-title")
        
        self.show_history = not self.show_history
        
        if self.show_history:
            history_container.display = True
            history_title.display = True
        else:
            history_container.display = False
            history_title.display = False


if __name__ == "__main__":
    app = MindMapApp()
    app.run()
