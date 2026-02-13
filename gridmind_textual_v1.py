#!/usr/bin/env python3
"""
Mind Mapper TUI - Textual 기반 대화형 마인드맵 도구
"""
import re
import csv
from datetime import datetime
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, Tree, Input, Button, 
    Static, Label, TextArea
)
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.binding import Binding
from textual.reactive import reactive


class MindMapApp(App):
    """마인드맵 TUI 애플리케이션"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        layout: horizontal;
        height: 100%;
    }
    
    #left-panel {
        width: 40%;
        border: solid $primary;
        padding: 1;
    }
    
    #right-panel {
        width: 60%;
        border: solid $accent;
        padding: 1;
    }
    
    #tree-container {
        height: 1fr;
        border: solid $success;
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
    
    Input {
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
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+s", "save_graph", "Save", show=True),
        Binding("ctrl+r", "reset", "Reset", show=True),
    ]
    
    # 상태 관리
    current_phase = reactive("init")  # init, collecting, complete
    current_index = reactive(0)
    current_parent = reactive("")
    
    def __init__(self):
        super().__init__()
        self.X = []
        self.question = ""
        self.question_words = []
        self.const_spl = []
        self.current_Y = []
        self.current_child_index = 0
        self.remaining_children = []
    
    def compose(self) -> ComposeResult:
        """UI 구성"""
        yield Header()
        
        with Container(id="main-container"):
            # 왼쪽 패널 - 트리 시각화
            with Vertical(id="left-panel"):
                yield Static("🧠 Mind Structure", classes="title")
                with ScrollableContainer(id="tree-container"):
                    yield Tree("Mindmap", id="mindmap-tree")
            
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
                        placeholder="Ask Yourself! (예: 효율적인 시스템이란?)",
                        id="question-input"
                    )
                    yield Label("", id="relation-label")
                    yield Input(
                        placeholder="관계를 입력하세요...",
                        id="notes-input",
                        disabled=True
                    )
        
        # 하단 컨트롤
        with Horizontal(id="controls"):
            yield Button("Start", id="start-btn", variant="success")
            yield Button("Next →", id="next-btn", variant="primary", disabled=True)
            yield Button("Skip", id="skip-btn", variant="default", disabled=True)
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
        elif button_id == "save-btn":
            self.action_save_graph()
        elif button_id == "reset-btn":
            self.action_reset()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Enter 키 처리"""
        if event.input.id == "question-input" and self.current_phase == "init":
            self.start_mapping()
        elif event.input.id == "notes-input" and self.current_phase == "collecting":
            self.process_current()
    
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
        self.query_one("#notes-input").disabled = False
        
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
        
        relation_text = f"💭 '{self.current_parent}' ↔ '{current_child}' 관계:"
        self.query_one("#relation-label").update(relation_text)
        
        self.update_status(
            f"진행 중... ({self.current_child_index + 1}/{len(self.remaining_children)} 관계)",
            "success"
        )
        
        # 입력 필드 포커스
        notes_input = self.query_one("#notes-input", Input)
        notes_input.value = ""
        notes_input.focus()
    
    def process_current(self):
        """현재 입력 처리"""
        notes_input = self.query_one("#notes-input", Input)
        notes = notes_input.value.strip()
        
        if notes:
            current_child = self.remaining_children[self.current_child_index]
            Z = [s for s in re.split(r"\W+", notes) if s]
            self.current_Y.append([current_child, Z])
            
            self.notify(f"✓ 기록됨: {current_child} → {', '.join(Z)}")
        
        self.current_child_index += 1
        self.prompt_next_relation()
    
    def skip_current(self):
        """현재 관계 건너뛰기"""
        current_child = self.remaining_children[self.current_child_index]
        self.current_Y.append([current_child, []])
        self.notify(f"⊘ 건너뜀: {current_child}")
        
        self.current_child_index += 1
        self.prompt_next_relation()
    
    def complete_mapping(self):
        """매핑 완료"""
        self.current_phase = "complete"
        
        self.query_one("#notes-input").disabled = True
        self.query_one("#next-btn").disabled = True
        self.query_one("#skip-btn").disabled = True
        self.query_one("#save-btn").disabled = False
        
        self.update_status("✨ 완성! 저장할 수 있습니다.", "success")
        self.query_one("#progress-label").update("")
        self.query_one("#relation-label").update("")
        
        self.update_tree()
        self.notify("🎉 마인드맵 생성 완료!")
    
    def update_tree(self):
        """트리 UI 업데이트"""
        tree = self.query_one("#mindmap-tree", Tree)
        tree.clear()
        
        root = tree.root
        root.expand()
        
        for top_item in self.X:
            if not top_item:
                continue
                
            top_node = top_item[0]
            top_branch = root.add(f"🔵 {top_node}", expand=True)
            
            for mid_item in top_item[1:]:
                if not isinstance(mid_item, list) or len(mid_item) < 2:
                    continue
                    
                mid_node = mid_item[0]
                mid_branch = top_branch.add(f"🟡 {mid_node}", expand=True)
                
                for leaf in mid_item[1]:
                    mid_branch.add_leaf(f"🟢 {leaf}")
    
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
        """그래프 저장"""
        if not self.X:
            self.notify("저장할 데이터가 없습니다!", severity="warning")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV 저장
        csv_filename = f"mindmap_{timestamp}.csv"
        self.save_csv(csv_filename)
        
        # DOT 저장
        dot_filename = f"mindmap_{timestamp}.dot"
        self.save_dot(dot_filename)
        
        self.notify(f"💾 저장 완료!\n{csv_filename}\n{dot_filename}", severity="information")
        self.update_status(f"✓ 파일 저장됨: {csv_filename}, {dot_filename}", "success")
    
    def save_csv(self, filename: str):
        """CSV 파일로 저장"""
        edges = []
        for top_item in self.X:
            top_node = top_item[0]
            
            for mid_item in top_item[1:]:
                if not isinstance(mid_item, list) or len(mid_item) < 2:
                    continue
                    
                mid_node = mid_item[0]
                edge_label = f"{top_node}_{mid_node}"
                
                edges.append((top_node, edge_label, mid_node))
                
                for leaf in mid_item[1]:
                    leaf_label = f"{top_node}_{mid_node}_{leaf}"
                    edges.append((edge_label, leaf_label, leaf))
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['from', 'to', 'label'])
            writer.writerows(edges)
    
    def save_dot(self, filename: str):
        """DOT 파일로 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('digraph G {\n')
            f.write('  rankdir=LR;\n')
            f.write('  node [shape=box, fontname="Malgun Gothic"];\n\n')
            
            for top_item in self.X:
                top_node = top_item[0]
                
                for mid_item in top_item[1:]:
                    if not isinstance(mid_item, list) or len(mid_item) < 2:
                        continue
                        
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
        
        # UI 초기화
        self.query_one("#question-input", Input).value = ""
        self.query_one("#question-input").disabled = False
        self.query_one("#notes-input", Input).value = ""
        self.query_one("#notes-input").disabled = True
        
        self.query_one("#start-btn").disabled = False
        self.query_one("#next-btn").disabled = True
        self.query_one("#skip-btn").disabled = True
        self.query_one("#save-btn").disabled = True
        
        self.query_one("#status-label").update("시작하려면 질문을 입력하세요")
        self.query_one("#progress-label").update("")
        self.query_one("#relation-label").update("")
        
        # 트리 초기화
        tree = self.query_one("#mindmap-tree", Tree)
        tree.clear()
        tree.root.set_label("Mindmap")
        
        self.query_one("#question-input").focus()
        self.notify("🔄 초기화 완료")


if __name__ == "__main__":
    app = MindMapApp()
    app.run()
