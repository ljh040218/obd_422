# CAN 통신 데이터 관련 정리

raw TRC, DBC, 신호 정의와 분석 코드입니다

CAN을 처음 접하신다면 goodtoknow.pdf에 정리한 자료를 가볍게 참고해보셔도 좋을 것 같습니다

## 파일 구성

| 파일/폴더 | 역할 |
|---|---|
| run_all.py | TRC → DBC를 이용한 CAN 해석 → MF4 → CSV → plot 전체 실행 |
| analyze_mf4.py | 저장된 MF4 읽기 |
| codes/ | 데이터 처리하는 코드들 |
| requirements.txt | 필요한 라이브러리 버전 |
| data/ | 주행 원본 TRC |
| definitions/hyundai_kia_generic.dbc | CAN 신호 정의 파일 |
| definitions/message_definitions.csv | DBC 메시지 ID, 길이, 송수신 노드 정의 |
| definitions/signal_definitions.csv | 전체 DBC 신호 1,325개 정의 |
| definitions/plot_signals.json | 시각화와 선택 csv에 사용할 신호 이름 |

## 실행 예

Python 3.12 필요

`\(본인 경로)\python.exe -m pip install -r requirements.txt`

`\(본인 경로)\python.exe run_all.py`

시각화 결과와 신호 리스트를 확인 할 수 있습니다

수신한 CAN ID를 기준으로 DBC에 정의된 신호를 해석합니다. 

csv 두 개는 사용한 DBC에서 생성되어 결과 폴더의 definitions에 저장됩니다.


다른 결과 폴더를 쓰려면:

`\Scripts\python.exe run_all.py --output-dir results_my_experiment`



다른 TRC와 DBC를 쓰려면:

`\Scripts\python.exe run_all.py --input data/drive_01.trc --dbc definitions/hyundai_kia_generic.dbc --output-dir results_01`

입력 TRC, DBC, 출력 경로는 절대경로와 상대경로 모두 사용할 수 있습니다. 입력해서 쓰세요.

## 저장된 MF4 읽기

위 전체 실행으로 MF4를 만든 다음 다시 읽을 수 있습니다. 

`--mf4`에 다른 수치 신호 MF4 경로를 넣어도 됩니다.

`\Scripts\python.exe analyze_mf4.py --mf4 results/drive_01/drive_01.mf4 --output-dir mf4_inspection_01`

* 전체 신호 목록, 수치 신호의 CSV, 처리 요약이 생성됩니다. 

원하는 신호만 읽으려면 뒤에 `--signals EMS11.N EMS11.VS`처럼 신호명을 넣으면 됩니다.

`results/signal_availability.csv`는 정의된 신호의 실제 관측 정보를 확인합니다. 

`signals_aligned.csv`는 시간+전체 신호, selected_signals.csv는 시간+선택한 신호입니다.

`signal_inventory.csv`에 실제 읽힌 전체 신호의 통계와 주기가 있습니다.

MF4는 수신 시간을 보존합니다. 분석용 CSV는 기본 0.01초 간격으로 맞췄고 

첫 수신 전이나 마지막 수신 후 0.5초가 넘는 구간은 빈칸으로 남겼습니다. 

레코딩 원래 시간의 csv도 필요하면 실행 명령 뒤에 `--raw-csv`를 추가하심 됩니다.

DBC에 정의되지 않은 CAN ID는 넘기고 frames_unresolved.csv에 따로 저장합니다. 

전체 송수신 프레임은 frames_raw.csv에 저장합니다.