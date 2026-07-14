"""views/login.py — Premium Enterprise Login Page"""
import streamlit as st
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.auth_service import auth
from config.settings   import settings


def render() -> None:
    # Override the page background + hide sidebar
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
      background: linear-gradient(160deg, #0E1A2E 0%, #1B3050 60%, #162644 100%) !important;
    }
    .block-container { padding: 3rem 1rem 2rem !important; }
    [data-testid="stSidebar"] { display: none !important; }

    /* Make Sign In button blue on login page */
    .stFormSubmitButton > button {
      background:    #2563EB !important;
      border-color:  #2563EB !important;
      color:         #FFFFFF !important;
      font-size:     15px !important;
      font-weight:   600 !important;
      border-radius: 10px !important;
      height:        48px !important;
      box-shadow:    0 3px 12px rgba(37,99,235,0.30) !important;
      transition:    all 0.2s ease !important;
      letter-spacing: 0.02em !important;
    }
    .stFormSubmitButton > button:hover {
      background:   #1D4ED8 !important;
      box-shadow:   0 5px 20px rgba(37,99,235,0.40) !important;
      transform:    translateY(-1px) !important;
    }
    /* Input fields */
    .stTextInput > label {
      color:       #374151 !important;
      font-size:   13px !important;
      font-weight: 500 !important;
    }
    .stTextInput > div > div > input {
      height:        44px !important;
      border-radius: 10px !important;
      border-color:  #D1D5DB !important;
      font-size:     14px !important;
      color:         #111827 !important;
      background:    #FFFFFF !important;
    }
    .stTextInput > div > div > input:focus {
      border-color: #2563EB !important;
      box-shadow:   0 0 0 3px rgba(37,99,235,0.12) !important;
    }
    /* Create Account button */
    .main .stButton > button { border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

    # Center layout
    _, col, _ = st.columns([1, 1.1, 1])

    with col:
        # Logo + Brand header
        st.markdown("""
        <div style="text-align:center;margin-bottom:32px">
          <div style="display:inline-flex;align-items:center;justify-content:center;
               width:60px;height:60px;
               background:linear-gradient(135deg,#1D4ED8,#3B82F6);
               border-radius:16px;
               box-shadow:0 8px 24px rgba(37,99,235,0.45);
               margin-bottom:18px">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"
                stroke="#fff" stroke-width="2.5" stroke-linecap="round"
                stroke-linejoin="round"/>
            </svg>
          </div>
          <div style="font-size:22px;font-weight:800;color:#F1F5F9;
               letter-spacing:-0.02em;margin-bottom:6px">
            IndustrialMaint AI
          </div>
          <div style="font-size:12px;color:#94A3B8;letter-spacing:0.03em">
            Hybrid AI Predictive Maintenance Platform
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Login card
        st.markdown("""
        <div style="background:rgba(255,255,255,0.98);
             backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
             border-radius:20px;padding:36px 40px 32px;
             box-shadow:0 24px 64px rgba(0,0,0,0.40),0 4px 16px rgba(0,0,0,0.12);
             border:1px solid rgba(255,255,255,0.70)">
          <div style="font-size:22px;font-weight:700;color:#0F172A;margin-bottom:4px">
            Welcome back
          </div>
          <div style="font-size:13px;color:#6B7280;margin-bottom:24px">
            Sign in to your account to continue
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Error
        err = auth.get_auth_error()
        if err:
            st.markdown(
                f'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;'
                f'padding:10px 14px;margin-bottom:12px;font-size:13px;color:#B91C1C">'
                f'⚠️ {err}</div>',
                unsafe_allow_html=True,
            )

        # Demo badge
        if settings.demo_mode:
            st.markdown(
                f'<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;'
                f'padding:10px 14px;margin-bottom:16px;font-size:12px;color:#1D4ED8">'
                f'<b>✨ Demo Mode Active</b> — Use:&nbsp;'
                f'<code style="background:#DBEAFE;padding:1px 6px;border-radius:4px">'
                f'{settings.demo_email}</code> /&nbsp;'
                f'<code style="background:#DBEAFE;padding:1px 6px;border-radius:4px">'
                f'{settings.demo_password}</code></div>',
                unsafe_allow_html=True,
            )

        with st.form("login_form"):
            email    = st.text_input(
                "Email address", placeholder="engineer@company.com", key="login_email"
            )
            st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)
            password = st.text_input(
                "Password", type="password", placeholder="••••••••", key="login_pw"
            )
            st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

            col_rem, col_forgot = st.columns([1, 1])
            with col_rem:
                st.checkbox("Remember me", key="login_remember")
            with col_forgot:
                st.markdown(
                    '<div style="text-align:right;padding-top:6px">'
                    '<span style="font-size:12px;color:#2563EB;cursor:pointer">'
                    'Forgot password?</span></div>',
                    unsafe_allow_html=True,
                )

            st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
            submitted = st.form_submit_button(
                "Sign In →", use_container_width=True, type="primary"
            )

        if submitted:
            if not email or not password:
                st.error("Please enter your email and password.")
            else:
                with st.spinner("Authenticating..."):
                    if auth.login(email.strip(), password):
                        st.session_state.page = "Dashboard"
                        st.rerun()
                    else:
                        st.error(f"⚠️ {auth.get_auth_error()}")

        # Register link
        st.markdown(
            '<div style="text-align:center;margin-top:18px;margin-bottom:10px;'
            'font-size:12px;color:#6B7280">Don\'t have an account?</div>',
            unsafe_allow_html=True,
        )

        if st.button(
            "Create Account →", use_container_width=True,
            type="secondary", key="go_register"
        ):
            st.session_state.auth_page = "register"
            st.rerun()

        # Footer
        st.markdown("""
        <div style="text-align:center;margin-top:28px;font-size:11px;color:#64748B">
          MIT VIT Research · IEEE Conference 2025 ·
          <span style="color:#2563EB">IndustrialMaint AI v3.0</span>
        </div>
        """, unsafe_allow_html=True)
