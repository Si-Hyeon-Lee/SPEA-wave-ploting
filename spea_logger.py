'''

'''
import sys
import os
import glob
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QTextEdit
from PyQt5.QtCore import QTimer

class LogMonitorWindow(QMainWindow):
    def __init__(self, directory="."):
        super().__init__()
        self.setWindowTitle("DLK File Monitoring v1.3.1")
        self.setGeometry(200, 200, 600, 400)

        # 텍스트 영역
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.setCentralWidget(self.text_edit)

        # 모니터링 대상 디렉토리 설정
        self.directory = directory

        # 상태 관리 변수
        self.dlk_exists = False   # 현재 .dlk 파일이 존재하는지 여부
        self.last_position = 0    # 파일 포인터 위치

        # QTimer를 통해 1초마다 디렉토리 확인
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_dlk_file)
        self.timer.start(3000)

    def check_dlk_file(self):
        # 디렉토리 내의 .dlk 파일 목록 확인
        dlk_files = glob.glob(os.path.join(self.directory, "*.dlk"))

        if not dlk_files:
            # .dlk 파일이 없는 경우
            if self.dlk_exists:
                # 기존에 파일이 있었는데 지금은 없으므로, 화면 초기화
                self.text_edit.clear()
                self.dlk_exists = False
                self.last_position = 0
            # 파일이 없고 이전에도 없었다면(대기 상태), 별도 행동 없음
        else:
            # .dlk 파일이 있는 경우 (디렉토리에 하나만 있다고 가정)
            dlk_file_path = dlk_files[0]

            if not self.dlk_exists:
                # 신규 생성된 .dlk 파일로 인식
                self.dlk_exists = True
                self.last_position = 0
                # 처음부터 읽어오기
                self.read_new_data(dlk_file_path, from_start=True)
            else:
                # 이미 감시 중인 상황이므로 추가된 내용만 읽어오기
                self.read_new_data(dlk_file_path, from_start=False)

    def read_new_data(self, file_path, from_start=False):
        """파일의 특정 위치부터 새 데이터(또는 전체)를 읽어와 화면에 표시한다."""
        mode = "r"
        with open(file_path, mode, encoding="utf-8") as f:
            # 파일 처음부터 다시 읽거나, 마지막 포인터 위치부터 읽음
            if from_start:
                f.seek(0)
            else:
                f.seek(self.last_position)

            new_data = f.read()
            if new_data:
                lines = new_data.split('\n')
                for line in lines:
                    self.text_edit.append(line)
                # 파일 포인터 위치 갱신
                self.last_position = f.tell()
def handle_exception(exc_type, exc_value, exc_traceback):
    """예외 발생 시 로그 파일에 기록"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    error_message = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    with open("error_log.txt", "a", encoding="utf-8") as f:
        f.write(f"Unhandled Exception:\n{error_message}\n")

    print("Unhandled Exception:", error_message)

# 전역 예외 처리
sys.excepthook = handle_exception
def main():
    app = QApplication(sys.argv)
    window = LogMonitorWindow(directory="C:\ATOSC2\WKSINFO\Temp")
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


