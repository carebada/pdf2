import streamlit as st
import pdfplumber, pandas as pd, re
from jinja2 import Template
import io
import base64
import hashlib
from datetime import datetime, date, timedelta
from typing import Dict

# =====================================
# 클라우드용 사용자 관리 시스템
# =====================================

class CloudUserManager:
    """클라우드 환경용 사용자 관리"""
    
    def __init__(self):
        self.users = {
            "admin": {
                "password_hash": "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",  # admin123
                "full_name": "시스템 관리자",
                "role": "admin",
                "daily_limit": -1,
                "monthly_limit": -1,
                "end_date": "2025-12-31"
            },
            "user1": {
                "password_hash": "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f",  # password123
                "full_name": "일반 사용자",
                "role": "user", 
                "daily_limit": 5,
                "monthly_limit": 50,
                "end_date": "2025-12-31"
            },
            "trial1": {
                "password_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",  # hello
                "full_name": "체험판 사용자",
                "role": "user",
                "daily_limit": 3,
                "monthly_limit": 20,
                "end_date": "2025-07-01"
            },
            "premium1": {
                "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # premium123
                "full_name": "프리미엄 사용자",
                "role": "user",
                "daily_limit": 20,
                "monthly_limit": 500,
                "end_date": "2025-12-31"
            }
        }
        self.init_session_data()
    
    def init_session_data(self):
        """세션 데이터 초기화"""
        if 'usage_data' not in st.session_state:
            st.session_state.usage_data = {}
        if 'user_management_settings' not in st.session_state:
            st.session_state.user_management_settings = {
                "app_title": "PDF 진료이력 분석기 v3.0",
                "admin_contact": "관리자 연락처: admin@example.com"
            }
    
    def authenticate_user(self, username: str, password: str) -> Dict:
        """사용자 인증"""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username not in self.users:
            return {"success": False, "message": "존재하지 않는 사용자입니다."}
        
        user = self.users[username]
        
        if user["password_hash"] != password_hash:
            return {"success": False, "message": "비밀번호가 잘못되었습니다."}
        
        # 기간 확인
        today = date.today()
        end_date = datetime.strptime(user["end_date"], "%Y-%m-%d").date()
        
        if today > end_date:
            return {"success": False, "message": "사용 기간이 만료되었습니다."}
        
        # 사용량 확인
        usage_status = self.check_usage_limits(username)
        if not usage_status["can_use"]:
            return {"success": False, "message": usage_status["message"]}
        
        user_data = user.copy()
        user_data["username"] = username
        user_data["success"] = True
        user_data["usage_status"] = usage_status
        
        return user_data
    
    def check_usage_limits(self, username: str) -> Dict:
        """사용 제한 확인"""
        if username not in self.users:
            return {"can_use": False, "message": "사용자를 찾을 수 없습니다."}
        
        user = self.users[username]
        today = date.today().strftime("%Y-%m-%d")
        month = date.today().strftime("%Y-%m")
        
        # 세션에서 사용량 데이터 로드
        if username not in st.session_state.usage_data:
            st.session_state.usage_data[username] = {"daily": {}, "monthly": {}, "total": 0}
        
        user_usage = st.session_state.usage_data[username]
        
        # 오늘 사용량
        daily_usage = user_usage["daily"].get(today, 0)
        
        # 이번 달 사용량  
        monthly_usage = user_usage["monthly"].get(month, 0)
        
        # 총 사용량
        total_usage = user_usage["total"]
        
        # 제한 확인
        daily_limit = user["daily_limit"]
        monthly_limit = user["monthly_limit"]
        
        if daily_limit > 0 and daily_usage >= daily_limit:
            return {
                "can_use": False,
                "message": f"일일 사용 한도 초과 ({daily_usage}/{daily_limit})",
                "daily_usage": daily_usage,
                "daily_limit": daily_limit,
                "monthly_usage": monthly_usage,
                "monthly_limit": monthly_limit,
                "total_usage": total_usage
            }
        
        if monthly_limit > 0 and monthly_usage >= monthly_limit:
            return {
                "can_use": False,
                "message": f"월간 사용 한도 초과 ({monthly_usage}/{monthly_limit})",
                "daily_usage": daily_usage,
                "daily_limit": daily_limit,
                "monthly_usage": monthly_usage,
                "monthly_limit": monthly_limit,
                "total_usage": total_usage
            }
        
        return {
            "can_use": True,
            "message": "사용 가능",
            "daily_usage": daily_usage,
            "daily_limit": daily_limit,
            "monthly_usage": monthly_usage,
            "monthly_limit": monthly_limit,
            "total_usage": total_usage
        }
    
    def log_usage(self, username: str):
        """사용량 기록"""
        today = date.today().strftime("%Y-%m-%d")
        month = date.today().strftime("%Y-%m")
        
        if username not in st.session_state.usage_data:
            st.session_state.usage_data[username] = {"daily": {}, "monthly": {}, "total": 0}
        
        user_usage = st.session_state.usage_data[username]
        
        # 사용량 증가
        user_usage["daily"][today] = user_usage["daily"].get(today, 0) + 1
        user_usage["monthly"][month] = user_usage["monthly"].get(month, 0) + 1
        user_usage["total"] += 1
    
    def get_user_list(self) -> Dict:
        """사용자 목록 조회 (관리자용)"""
        return {username: {
            "full_name": info["full_name"],
            "role": info["role"],
            "daily_limit": info["daily_limit"],
            "monthly_limit": info["monthly_limit"],
            "end_date": info["end_date"]
        } for username, info in self.users.items()}

# =====================================
# 관리자 페이지
# =====================================

def admin_dashboard(user_manager):
    """관리자 대시보드"""
    st.title("👨‍💼 관리자 대시보드")
    
    tab1, tab2, tab3 = st.tabs(["📊 현황", "👥 사용자 관리", "📈 사용 통계"])
    
    with tab1:
        st.subheader("📊 시스템 현황")
        
        # 전체 사용자 수
        total_users = len(user_manager.users)
        active_users = sum(1 for user in user_manager.users.values() 
                          if datetime.strptime(user["end_date"], "%Y-%m-%d").date() >= date.today())
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("전체 사용자", total_users)
        with col2:
            st.metric("활성 사용자", active_users)
        with col3:
            total_usage_today = sum(
                data.get("daily", {}).get(date.today().strftime("%Y-%m-%d"), 0)
                for data in st.session_state.usage_data.values()
            )
            st.metric("오늘 총 사용량", total_usage_today)
        
        st.subheader("⚙️ 시스템 설정")
        
        with st.form("system_settings"):
            new_title = st.text_input("앱 제목", value=st.session_state.user_management_settings["app_title"])
            new_contact = st.text_input("관리자 연락처", value=st.session_state.user_management_settings["admin_contact"])
            
            if st.form_submit_button("설정 저장"):
                st.session_state.user_management_settings["app_title"] = new_title
                st.session_state.user_management_settings["admin_contact"] = new_contact
                st.success("설정이 저장되었습니다!")
    
    with tab2:
        st.subheader("👥 사용자 목록")
        
        # 사용자 목록 표시
        user_list = user_manager.get_user_list()
        
        for username, info in user_list.items():
            with st.expander(f"👤 {info['full_name']} (@{username})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**역할:** {info['role']}")
                    st.write(f"**일일 한도:** {info['daily_limit'] if info['daily_limit'] > 0 else '무제한'}")
                    st.write(f"**월간 한도:** {info['monthly_limit'] if info['monthly_limit'] > 0 else '무제한'}")
                
                with col2:
                    st.write(f"**만료일:** {info['end_date']}")
                    
                    # 사용량 정보
                    if username in st.session_state.usage_data:
                        usage_info = st.session_state.usage_data[username]
                        today_usage = usage_info.get("daily", {}).get(date.today().strftime("%Y-%m-%d"), 0)
                        total_usage = usage_info.get("total", 0)
                        st.write(f"**오늘 사용:** {today_usage}")
                        st.write(f"**총 사용:** {total_usage}")
                    else:
                        st.write("**사용 기록:** 없음")
    
    with tab3:
        st.subheader("📈 사용 통계")
        
        # 일별 사용량 차트
        daily_stats = {}
        for username, usage_data in st.session_state.usage_data.items():
            for date_str, count in usage_data.get("daily", {}).items():
                daily_stats[date_str] = daily_stats.get(date_str, 0) + count
        
        if daily_stats:
            df_stats = pd.DataFrame(list(daily_stats.items()), columns=["날짜", "사용량"])
            df_stats["날짜"] = pd.to_datetime(df_stats["날짜"])
            df_stats = df_stats.sort_values("날짜")
            
            st.subheader("📅 일별 사용량")
            st.line_chart(df_stats.set_index("날짜"))
        else:
            st.info("아직 사용 데이터가 없습니다.")
        
        # 사용자별 사용량
        st.subheader("👥 사용자별 사용량")
        user_usage_data = []
        for username, usage_data in st.session_state.usage_data.items():
            user_info = user_manager.users.get(username, {})
            user_usage_data.append({
                "사용자": f"{user_info.get('full_name', username)} (@{username})",
                "총 사용량": usage_data.get("total", 0),
                "오늘 사용량": usage_data.get("daily", {}).get(date.today().strftime("%Y-%m-%d"), 0)
            })
        
        if user_usage_data:
            df_user_usage = pd.DataFrame(user_usage_data)
            st.dataframe(df_user_usage, use_container_width=True)
        else:
            st.info("사용 기록이 없습니다.")

# =====================================
# 기존 PDF 처리 함수들 (그대로 유지)
# =====================================

def contains_pharmacy(val):
    if not isinstance(val, str): return False
    no_space = re.sub(r'\s+', '', val)
    return '약국' in no_space

def clean_code(code):
    return re.sub(r'[^A-Z0-9]', '', code)[1:4] if code and code and code[0]=='A' else code[:3]

def clean_name(name):
    if not isinstance(name, str): return ''
    name = re.sub(r'\s+', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'약국', '', name)
    return name.strip()

def make_grouped_data(rows):
    df = pd.DataFrame(rows, columns=['순번','진료일','의료기관','진료과','입원/외래','상병코드','병명','내원일수','총진료비','보험혜택','본인부담'])
    df = df[~df['의료기관'].fillna('').apply(contains_pharmacy)]
    df = df[~df['병명'].fillna('').apply(contains_pharmacy)]
    df['병명'] = df['병명'].fillna('').apply(clean_name)
    df = df[df['병명'] != '']
    df['상병그룹코드'] = df['상병코드'].apply(clean_code)
    df['내원일수'] = df['내원일수'].astype(int)
    df['진료일'] = pd.to_datetime(df['진료일'], errors='coerce')
    df = df[df['상병그룹코드'].notnull()]
    group_rows = []
    groups = {}
    for code, sub in df.groupby('상병그룹코드'):
        in_pat = sub[sub['입원/외래'].str.contains('입원')]
        out_pat = sub[sub['입원/외래'].str.contains('외래')]
        group_name = sub.iloc[0]['병명']
        date_range = sub['진료일'].sort_values()
        period = f"{date_range.iloc[0].strftime('%Y-%m-%d')} ~ {date_range.iloc[-1].strftime('%Y-%m-%d')}" if len(date_range) else "-"
        in_days = in_pat['내원일수'].sum()
        out_days = out_pat['내원일수'].sum()
        in_pat_flag = in_pat.shape[0] > 0
        out_pat_flag = out_pat.shape[0] > 0
        out_7_flag = out_days >= 7
        group_rows.append({
            'code': code,
            'name': group_name,
            'period': period,
            'in_days': in_days,
            'out_days': out_days,
            'in_pat': in_pat_flag,
            'out_pat': out_pat_flag,
            'out_7_flag': out_7_flag
        })
        details = []
        for _, r in in_pat.sort_values('진료일', ascending=False).iterrows():
            details.append({'date':r['진료일'].strftime('%Y-%m-%d'),'type':'입원','hospital':r['의료기관'],'name':r['병명'],'days':r['내원일수']})
        for _, r in out_pat.sort_values('진료일', ascending=False).iterrows():
            details.append({'date':r['진료일'].strftime('%Y-%m-%d'),'type':'외래','hospital':r['의료기관'],'name':r['병명'],'days':r['내원일수']})
        groups[code] = {
            'name': group_name,
            'period': period,
            'in_days': in_days,
            'out_days': out_days,
            'details': details,
            'in_pat': in_pat_flag,
            'out_pat': out_pat_flag
        }
    def sort_key(g):
        if g['in_pat']:
            return (0, -g['in_days'], -g['out_days'])
        elif g['out_7_flag']:
            return (1, -g['out_days'], 0)
        else:
            return (2, 0, 0)
    group_rows = sorted(group_rows, key=sort_key)
    sorted_codes = [row['code'] for row in group_rows]
    groups_sorted = {code: groups[code] for code in sorted_codes}
    return group_rows, groups_sorted

def extract_pdf_table(pdf_bytes):
    rows = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table: continue
            for row in table:
                if row and row[0] and str(row[0]).strip().isdigit():
                    rows.append(row)
    return rows

# =====================================
# 메인 애플리케이션
# =====================================

def main():
    st.set_page_config(
        page_title="PDF 진료이력 분석기 v3.0",
        page_icon="🏥",
        layout="wide"
    )
    
    # 사용자 관리자 초기화
    user_manager = CloudUserManager()
    
    # 세션 상태 초기화
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    # 로그인 페이지
    if not st.session_state.authenticated:
        # 제목 표시
        app_title = st.session_state.user_management_settings.get("app_title", "PDF 진료이력 분석기 v3.0")
        st.title(f"🏥 {app_title}")
        st.subheader("🔐 사용자 인증이 필요한 서비스")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("---")
            
            # 로그인 폼
            with st.form("login_form"):
                st.subheader("로그인")
                username = st.text_input("사용자명", placeholder="사용자명을 입력하세요")
                password = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    login_btn = st.form_submit_button("🔐 로그인", type="primary", use_container_width=True)
                
                if login_btn:
                    if username and password:
                        auth_result = user_manager.authenticate_user(username, password)
                        
                        if auth_result["success"]:
                            st.session_state.authenticated = True
                            st.session_state.user_info = auth_result
                            st.session_state.username = username
                            st.success("✅ 로그인 성공!")
                            st.rerun()
                        else:
                            st.error(f"❌ {auth_result['message']}")
                    else:
                        st.error("❌ 사용자명과 비밀번호를 모두 입력해주세요.")
            
            # 테스트 계정 안내
            with st.expander("💡 테스트 계정 안내", expanded=True):
                st.markdown("""
                **🔧 관리자 계정:**
                - 사용자명: `admin`
                - 비밀번호: `admin123`
                - 권한: 무제한 사용 + 관리자 페이지 접근
                
                **👤 일반 사용자:**
                - 사용자명: `user1`
                - 비밀번호: `password123`
                - 제한: 일 5회, 월 50회
                
                **🎯 체험판:**
                - 사용자명: `trial1`
                - 비밀번호: `hello`
                - 제한: 일 3회, 월 20회, 2025년 7월까지
                
                **💎 프리미엄:**
                - 사용자명: `premium1`
                - 비밀번호: `premium123`
                - 제한: 일 20회, 월 500회
                """)
        
        # 하단 연락처 정보
        st.markdown("---")
        contact_info = st.session_state.user_management_settings.get("admin_contact", "")
        if contact_info:
            st.info(f"📞 {contact_info}")
        
        return
    
    # 로그인 후 메인 화면
    user_info = st.session_state.user_info
    
    # 상단 헤더
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        app_title = st.session_state.user_management_settings.get("app_title", "PDF 진료이력 분석기 v3.0")
        st.title(f"🏥 {app_title}")
    
    with col2:
        st.info(f"👤 {user_info['full_name']}님")
        if user_info['role'] == 'admin':
            st.success("🔧 관리자")
    
    with col3:
        if st.button("🚪 로그아웃", type="secondary"):
            st.session_state.clear()
            st.rerun()
    
    # 관리자 메뉴
    if user_info['role'] == 'admin':
        with st.sidebar:
            st.header("🔧 관리자 메뉴")
            
            menu_choice = st.radio("메뉴 선택", [
                "🏠 메인 페이지",
                "👨‍💼 관리자 대시보드"
            ])
            
            if menu_choice == "👨‍💼 관리자 대시보드":
                admin_dashboard(user_manager)
                return
    
    # 사용 현황 표시
    usage_status = user_manager.check_usage_limits(user_info['username'])
    
    if usage_status['can_use']:
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            daily_text = f"{usage_status['daily_usage']}"
            if usage_status['daily_limit'] > 0:
                daily_text += f"/{usage_status['daily_limit']}"
            else:
                daily_text += "/무제한"
            st.metric("⏰ 오늘 사용", daily_text)
        
        with col2:
            monthly_text = f"{usage_status['monthly_usage']}"
            if usage_status['monthly_limit'] > 0:
                monthly_text += f"/{usage_status['monthly_limit']}"
            else:
                monthly_text += "/무제한"
            st.metric("📅 이번 달", monthly_text)
        
        with col3:
            st.metric("📊 총 사용", usage_status['total_usage'])
    
    else:
        st.error(f"⚠️ {usage_status['message']}")
        
        # 한도 초과시 안내
        contact_info = st.session_state.user_management_settings.get("admin_contact", "")
        if contact_info:
            st.info(f"💡 사용 한도 증가가 필요하시면 연락주세요: {contact_info}")
        
        if user_info['role'] != 'admin':
            st.stop()
    
    # =====================================
    # 메인 PDF 분석 기능
    # =====================================
    
    st.markdown("---")
    
    # 주의사항
    with st.expander("⚠️ 서비스 이용 주의사항", expanded=False):
        st.markdown("""
        **📋 이용 안내**
        - **개인 용도 제한**: 본 서비스는 개인의 본인 용도로만 사용 가능합니다.
        - **파일 보안**: 업로드하신 파일은 처리 후 즉시 삭제되며, 별도로 저장되지 않습니다.
        - **파일 품질**: 스캔본이나 편집된 파일의 경우 인식 오류가 발생할 수 있습니다.
        - **내용 인식 한계**: 업로드하신 내용 중 일부가 정확히 인식되지 않을 수 있습니다.
        - **진단명 표시 범위**: 화면에 표시되는 진단명은 주상병 코드(주진단)에 한정됩니다.
        - **조회 제외 항목**: 최근 치료(3개월 이내), 자동차사고 관련 치료, 미용 및 치과질환, 비급여 치료 등은 조회되지 않습니다.
        - **이용자 책임**: 서비스 이용 중 발생하는 모든 결과에 대한 책임은 이용자 본인에게 있습니다.
        """)

    # PDF 업로드
    st.subheader("📄 PDF 파일 업로드")
    pdf_file = st.file_uploader("PDF 파일을 업로드하세요", type=["pdf"])
    
    if pdf_file is not None:
        # 사용량 재체크
        current_usage = user_manager.check_usage_limits(user_info['username'])
        if not current_usage['can_use']:
            st.error(f"⚠️ {current_usage['message']}")
            st.stop()
        
        with st.spinner("📊 PDF 분석 중... 잠시만 기다려주세요."):
            try:
                # 사용량 기록
                user_manager.log_usage(user_info['username'])
                
                # 기존 PDF 분석 로직
                rows = extract_pdf_table(pdf_file.read())
                
                if not rows:
                    st.error("❌ PDF에서 테이블 데이터를 찾을 수 없습니다.")
                    return
                
                group_rows, groups = make_grouped_data(rows)
                
                if not group_rows:
                    st.error("❌ 분석할 수 있는 진료 데이터가 없습니다.")
                    return
                
                # HTML 템플릿 (기존과 동일)
                HTML_TEMPLATE = '''
                <!DOCTYPE html>
                <html lang="ko"><head><meta charset="UTF-8"><title>진료 이력 요약</title>
                <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; background:#f6f8fa; margin:0; padding:18px; }
                .section-title {font-size:1.25em; font-weight:bold; color:#3757d4; background:#f7f9fc; border-radius:11px; margin-bottom:11px; margin-top:2px; padding:7px 13px 6px 10px; box-shadow:0 2px 8px #0001; letter-spacing:1px;}
                .top-table { width:100%; border-collapse:collapse; margin-bottom: 25px; box-shadow:0 2px 8px #0001; background:#fff; border-radius: 9px; overflow-x:auto;}
                .top-table th, .top-table td { padding:13px 6px; font-size:1.08em; border-bottom:1px solid #eee; text-align:center; white-space:nowrap; }
                .top-table th { background:#f1f1f8; color:#555; }
                .top-table tr:last-child td { border-bottom:none;}
                .label-in { background:#ffeaea; color:#d31717; font-weight:bold; border-radius:10px; padding:2px 9px; margin-left:4px; font-size:1em; display:inline-flex; align-items:center;}
                .label-out { background:#e7f6ff; color:#1876d1; font-weight:bold; border-radius:10px; padding:2px 9px; margin-left:4px; font-size:1em; display:inline-flex; align-items:center;}
                .label-out .hot { color:#ee2222; font-weight:bold; }
                .code-pill {
                  display: inline-block;
                  background: linear-gradient(90deg,#215fe6 80%,#5aa9f6 100%);
                  color: #fff;
                  font-weight: bold;
                  font-size: 1em;
                  border-radius: 14px;
                  padding: 2px 13px 2px 13px;
                  margin-right: 7px;
                  letter-spacing: 1px;
                  box-shadow: 0 1px 7px #22335424;
                }
                .group { background:#fff; margin-bottom:23px; border-radius:13px; box-shadow:0 2px 8px #0002; padding:13px 14px; max-width:950px; border:2px solid #f2f5fa;}
                .summary { margin-bottom: 7px; font-size:1.01em;}
                .disease { font-size:1.07em; font-weight:bold; color:#195; white-space:nowrap; }
                .period { color:#888; font-size:0.97em; margin-left:6px; white-space:nowrap;}
                table { width:100%; border-collapse:collapse; margin:8px 0 0 0;}
                th, td { padding:11px 6px; border-bottom:1px solid #eee; text-align:left; font-size:1.06em; white-space:nowrap;}
                th { background:#f7f7fa; color:#195; font-weight:bold;}
                .in-row { background:#fcecec; font-weight:bold;}
                .out-row { background:#e7f6ff;}
                .tag { border-radius:8px; font-size:0.96em; padding:2px 8px; color:#fff;}
                .tag-in { background:#e74c3c;}
                .tag-out { background:#1e81ce;}
                @media (max-width:700px){
                  .top-table, table {overflow-x:auto;display:block;}
                  .top-table th, .top-table td, th, td {
                    font-size: 0.98em !important;
                    padding: 10px 4px !important;
                    word-break:keep-all;
                    white-space:nowrap;
                  }
                  .disease, .period {
                    display:inline-block;
                    margin-top:0;
                    margin-left:6px;
                  }
                  .code-pill { font-size:1.02em; padding:2px 10px; margin-bottom:2px;}
                }
                .footer-note {
                  margin-top:40px;
                  font-size:1em;
                  color:#888;
                  text-align:center;
                  padding:18px 0 0 0;
                  letter-spacing:0.5px;
                }
                </style></head><body>
                <div class="section-title">🔎 한눈에 보는 집계 요약</div>
                <div style="overflow-x:auto;">
                <table class="top-table">
                  <thead>
                    <tr>
                      <th>상병코드</th>
                      <th>병명</th>
                      <th>치료기간</th>
                      <th>입원</th>
                      <th>외래</th>
                    </tr>
                  </thead>
                  <tbody>
                    {% for row in group_rows %}
                      <tr>
                        <td>
                          <span class="code-pill">{{ row['code'] }}</span>
                        </td>
                        <td style="word-break:keep-all; white-space:nowrap;">{{ row['name'] }}</td>
                        <td>{{ row['period'] }}</td>
                        <td>
                          {% if row['in_pat'] %}
                            <span class="label-in">❤️ 입원 {{ row['in_days'] }}일</span>
                          {% else %}
                            <span style="color:#bbb;">-</span>
                          {% endif %}
                        </td>
                        <td>
                          {% if row['out_pat'] %}
                            <span class="label-out">💙 외래
                              {% if row['out_7_flag'] %}
                                <span class="hot">{{ row['out_days'] }}일</span>
                              {% else %}
                                {{ row['out_days'] }}일
                              {% endif %}
                            </span>
                          {% else %}
                            <span style="color:#bbb;">-</span>
                          {% endif %}
                        </td>
                      </tr>
                    {% endfor %}
                  </tbody>
                </table>
                </div>
                <div class="section-title">📋 세부 진료내역</div>
                {% for code, group in groups.items() %}
                <div class="group">
                  <div class="summary" style="margin-bottom:10px;">
                    <span class="code-pill">{{ code }}</span>
                    <span class="disease">{{ group['name'] }}</span>
                    <span class="period">{{ group['period'] }}</span>
                  </div>
                  <div style="overflow-x:auto;">
                  <table>
                    <thead>
                      <tr>
                        <th>진료일</th>
                        <th>구분</th>
                        <th>의료기관</th>
                        <th>진단명</th>
                        <th>내원일수</th>
                      </tr>
                    </thead>
                    <tbody>
                      {% for item in group['details'] %}
                      <tr class="{{ 'in-row' if item['type']=='입원' else 'out-row' }}">
                        <td>{{ item['date'] }}</td>
                        <td><span class="tag {{ 'tag-in' if item['type']=='입원' else 'tag-out' }}">{{ item['type'] }}</span></td>
                        <td>{{ item['hospital'] }}</td>
                        <td>{{ item['name'] }}</td>
                        <td>{{ item['days'] }}</td>
                      </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                  </div>
                </div>
                {% endfor %}
                <div class="footer-note">
                  심평원 진료내역 정리 v3.0 (케어바다 제공) - 사용자 관리 시스템 적용
                </div>
                </body></html>
                '''
                
                html = Template(HTML_TEMPLATE).render(group_rows=group_rows, groups=groups)
                st.components.v1.html(html, height=900, scrolling=True)
                
                # 다운로드 링크
                b64 = base64.b64encode(html.encode('utf-8')).decode()
                href = f'<a href="data:text/html;base64,{b64}" download="진료이력_요약_{user_info["username"]}.html" style="font-weight:bold;font-size:1.05em;color:#174ba5;">[결과 HTML 다운로드]</a>'
                st.markdown(href, unsafe_allow_html=True)
                
                # 업데이트된 사용량 표시
                updated_usage = user_manager.check_usage_limits(user_info['username'])
                st.success(f"✅ 분석 완료! 오늘 사용량: {updated_usage['daily_usage']}{'' if updated_usage['daily_limit'] == -1 else '/' + str(updated_usage['daily_limit'])}")
                
            except Exception as e:
                st.error(f"❌ PDF 처리 실패: {e}")

if __name__ == "__main__":
    main()
