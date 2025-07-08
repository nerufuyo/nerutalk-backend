"""
Language constants and internationalization system for NeruTalk Backend.
Supports EN, ID, JP, KO, CN languages.
"""
from enum import Enum
from typing import Dict, Any


class SupportedLanguage(str, Enum):
    """Supported languages enum."""
    ENGLISH = "en"
    INDONESIAN = "id"
    JAPANESE = "jp"
    KOREAN = "ko"
    CHINESE = "cn"


# Default language
DEFAULT_LANGUAGE = SupportedLanguage.ENGLISH

# Language translations dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Authentication messages
    "auth_success": {
        "en": "Authentication successful",
        "id": "Autentikasi berhasil",
        "jp": "認証が成功しました",
        "ko": "인증이 성공했습니다",
        "cn": "认证成功"
    },
    "auth_failed": {
        "en": "Authentication failed",
        "id": "Autentikasi gagal",
        "jp": "認証に失敗しました",
        "ko": "인증에 실패했습니다",
        "cn": "认证失败"
    },
    "login_success": {
        "en": "Login successful",
        "id": "Login berhasil",
        "jp": "ログインが成功しました",
        "ko": "로그인이 성공했습니다",
        "cn": "登录成功"
    },
    "login_failed": {
        "en": "Invalid credentials",
        "id": "Kredensial tidak valid",
        "jp": "無効な認証情報",
        "ko": "잘못된 자격 증명",
        "cn": "凭据无效"
    },
    "logout_success": {
        "en": "Logout successful",
        "id": "Logout berhasil",
        "jp": "ログアウトが成功しました",
        "ko": "로그아웃이 성공했습니다",
        "cn": "登出成功"
    },
    "registration_success": {
        "en": "Registration successful",
        "id": "Registrasi berhasil",
        "jp": "登録が成功しました",
        "ko": "등록이 성공했습니다",
        "cn": "注册成功"
    },
    "user_not_found": {
        "en": "User not found",
        "id": "Pengguna tidak ditemukan",
        "jp": "ユーザーが見つかりません",
        "ko": "사용자를 찾을 수 없습니다",
        "cn": "用户未找到"
    },
    "email_already_exists": {
        "en": "Email already exists",
        "id": "Email sudah ada",
        "jp": "メールアドレスは既に存在します",
        "ko": "이메일이 이미 존재합니다",
        "cn": "电子邮件已存在"
    },
    "username_already_exists": {
        "en": "Username already exists",
        "id": "Username sudah ada",
        "jp": "ユーザー名は既に存在します",
        "ko": "사용자명이 이미 존재합니다",
        "cn": "用户名已存在"
    },
    "profile_updated": {
        "en": "Profile updated successfully",
        "id": "Profil berhasil diperbarui",
        "jp": "プロフィールが正常に更新されました",
        "ko": "프로필이 성공적으로 업데이트되었습니다",
        "cn": "个人资料更新成功"
    },

    # Chat messages
    "message_sent": {
        "en": "Message sent successfully",
        "id": "Pesan berhasil dikirim",
        "jp": "メッセージが正常に送信されました",
        "ko": "메시지가 성공적으로 전송되었습니다",
        "cn": "消息发送成功"
    },
    "message_delivered": {
        "en": "Message delivered",
        "id": "Pesan terkirim",
        "jp": "メッセージが配信されました",
        "ko": "메시지가 전달되었습니다",
        "cn": "消息已送达"
    },
    "message_read": {
        "en": "Message read",
        "id": "Pesan dibaca",
        "jp": "メッセージが読まれました",
        "ko": "메시지를 읽었습니다",
        "cn": "消息已读"
    },
    "chat_created": {
        "en": "Chat created successfully",
        "id": "Chat berhasil dibuat",
        "jp": "チャットが正常に作成されました",
        "ko": "채팅이 성공적으로 생성되었습니다",
        "cn": "聊天创建成功"
    },
    "user_typing": {
        "en": "is typing...",
        "id": "sedang mengetik...",
        "jp": "入力中...",
        "ko": "입력 중...",
        "cn": "正在输入..."
    },

    # Video call messages
    "call_initiated": {
        "en": "Call initiated",
        "id": "Panggilan dimulai",
        "jp": "通話が開始されました",
        "ko": "통화가 시작되었습니다",
        "cn": "通话已启动"
    },
    "call_answered": {
        "en": "Call answered",
        "id": "Panggilan dijawab",
        "jp": "通話に応答しました",
        "ko": "통화에 응답했습니다",
        "cn": "通话已接听"
    },
    "call_declined": {
        "en": "Call declined",
        "id": "Panggilan ditolak",
        "jp": "通話が拒否されました",
        "ko": "통화가 거절되었습니다",
        "cn": "通话被拒绝"
    },
    "call_ended": {
        "en": "Call ended",
        "id": "Panggilan berakhir",
        "jp": "通話が終了しました",
        "ko": "통화가 종료되었습니다",
        "cn": "通话已结束"
    },
    "incoming_call": {
        "en": "Incoming call",
        "id": "Panggilan masuk",
        "jp": "着信通話",
        "ko": "수신 통화",
        "cn": "来电"
    },

    # File and media messages
    "file_uploaded": {
        "en": "File uploaded successfully",
        "id": "File berhasil diunggah",
        "jp": "ファイルが正常にアップロードされました",
        "ko": "파일이 성공적으로 업로드되었습니다",
        "cn": "文件上传成功"
    },
    "file_deleted": {
        "en": "File deleted successfully",
        "id": "File berhasil dihapus",
        "jp": "ファイルが正常に削除されました",
        "ko": "파일이 성공적으로 삭제되었습니다",
        "cn": "文件删除成功"
    },
    "file_not_found": {
        "en": "File not found",
        "id": "File tidak ditemukan",
        "jp": "ファイルが見つかりません",
        "ko": "파일을 찾을 수 없습니다",
        "cn": "文件未找到"
    },
    "invalid_file_type": {
        "en": "Invalid file type",
        "id": "Tipe file tidak valid",
        "jp": "無効なファイルタイプ",
        "ko": "잘못된 파일 형식",
        "cn": "无效的文件类型"
    },
    "file_too_large": {
        "en": "File size too large",
        "id": "Ukuran file terlalu besar",
        "jp": "ファイルサイズが大きすぎます",
        "ko": "파일 크기가 너무 큽니다",
        "cn": "文件大小过大"
    },

    # Push notification messages
    "notification_sent": {
        "en": "Notification sent successfully",
        "id": "Notifikasi berhasil dikirim",
        "jp": "通知が正常に送信されました",
        "ko": "알림이 성공적으로 전송되었습니다",
        "cn": "通知发送成功"
    },
    "device_token_registered": {
        "en": "Device token registered",
        "id": "Token perangkat terdaftar",
        "jp": "デバイストークンが登録されました",
        "ko": "기기 토큰이 등록되었습니다",
        "cn": "设备令牌已注册"
    },
    "new_message": {
        "en": "New message from {sender_name}",
        "id": "Pesan baru dari {sender_name}",
        "jp": "{sender_name}からの新しいメッセージ",
        "ko": "{sender_name}님의 새 메시지",
        "cn": "来自{sender_name}的新消息"
    },

    # Location messages
    "location_updated": {
        "en": "Location updated successfully",
        "id": "Lokasi berhasil diperbarui",
        "jp": "位置が正常に更新されました",
        "ko": "위치가 성공적으로 업데이트되었습니다",
        "cn": "位置更新成功"
    },
    "location_share_started": {
        "en": "Location sharing started",
        "id": "Berbagi lokasi dimulai",
        "jp": "位置共有が開始されました",
        "ko": "위치 공유가 시작되었습니다",
        "cn": "位置分享已开始"
    },
    "location_share_stopped": {
        "en": "Location sharing stopped",
        "id": "Berbagi lokasi dihentikan",
        "jp": "位置共有が停止されました",
        "ko": "위치 공유가 중지되었습니다",
        "cn": "位置分享已停止"
    },
    "geofence_entry": {
        "en": "You have entered {geofence_name}",
        "id": "Anda telah memasuki {geofence_name}",
        "jp": "{geofence_name}に入りました",
        "ko": "{geofence_name}에 들어갔습니다",
        "cn": "您已进入{geofence_name}"
    },
    "geofence_exit": {
        "en": "You have exited {geofence_name}",
        "id": "Anda telah keluar dari {geofence_name}",
        "jp": "{geofence_name}から出ました",
        "ko": "{geofence_name}에서 나갔습니다",
        "cn": "您已离开{geofence_name}"
    },

    # Error messages
    "internal_server_error": {
        "en": "Internal server error",
        "id": "Kesalahan server internal",
        "jp": "内部サーバーエラー",
        "ko": "내부 서버 오류",
        "cn": "内部服务器错误"
    },
    "bad_request": {
        "en": "Bad request",
        "id": "Permintaan buruk",
        "jp": "不正なリクエスト",
        "ko": "잘못된 요청",
        "cn": "错误的请求"
    },
    "unauthorized": {
        "en": "Unauthorized access",
        "id": "Akses tidak sah",
        "jp": "不正なアクセス",
        "ko": "무단 액세스",
        "cn": "未经授权的访问"
    },
    "forbidden": {
        "en": "Access forbidden",
        "id": "Akses dilarang",
        "jp": "アクセスが禁止されています",
        "ko": "액세스가 금지됨",
        "cn": "访问被禁止"
    },
    "not_found": {
        "en": "Resource not found",
        "id": "Sumber daya tidak ditemukan",
        "jp": "リソースが見つかりません",
        "ko": "리소스를 찾을 수 없습니다",
        "cn": "资源未找到"
    },
    "validation_error": {
        "en": "Validation error",
        "id": "Kesalahan validasi",
        "jp": "検証エラー",
        "ko": "유효성 검사 오류",
        "cn": "验证错误"
    },

    # Success messages
    "operation_successful": {
        "en": "Operation completed successfully",
        "id": "Operasi berhasil diselesaikan",
        "jp": "操作が正常に完了しました",
        "ko": "작업이 성공적으로 완료되었습니다",
        "cn": "操作成功完成"
    },
    "data_saved": {
        "en": "Data saved successfully",
        "id": "Data berhasil disimpan",
        "jp": "データが正常に保存されました",
        "ko": "데이터가 성공적으로 저장되었습니다",
        "cn": "数据保存成功"
    },
    "data_deleted": {
        "en": "Data deleted successfully",
        "id": "Data berhasil dihapus",
        "jp": "データが正常に削除されました",
        "ko": "데이터가 성공적으로 삭제되었습니다",
        "cn": "数据删除成功"
    }
}


def get_text(key: str, language: SupportedLanguage = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Get translated text for the given key and language.
    
    Args:
        key (str): Translation key
        language (SupportedLanguage): Target language
        **kwargs: Additional parameters for string formatting
    
    Returns:
        str: Translated text
    """
    if key not in TRANSLATIONS:
        return key  # Return key if translation not found
    
    translation_dict = TRANSLATIONS[key]
    
    if language.value not in translation_dict:
        # Fallback to English if language not found
        text = translation_dict.get(DEFAULT_LANGUAGE.value, key)
    else:
        text = translation_dict[language.value]
    
    # Format string with provided kwargs
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            # If formatting fails, return unformatted text
            pass
    
    return text


def get_language_from_header(accept_language: str) -> SupportedLanguage:
    """
    Parse Accept-Language header and return supported language.
    
    Args:
        accept_language (str): Accept-Language header value
    
    Returns:
        SupportedLanguage: Detected supported language
    """
    if not accept_language:
        return DEFAULT_LANGUAGE
    
    # Parse Accept-Language header (simple implementation)
    languages = accept_language.lower().split(',')
    
    for lang in languages:
        lang_code = lang.strip().split(';')[0].split('-')[0]
        
        # Map common language codes
        if lang_code in ['en', 'eng']:
            return SupportedLanguage.ENGLISH
        elif lang_code in ['id', 'ind']:
            return SupportedLanguage.INDONESIAN
        elif lang_code in ['ja', 'jp', 'jpn']:
            return SupportedLanguage.JAPANESE
        elif lang_code in ['ko', 'kor']:
            return SupportedLanguage.KOREAN
        elif lang_code in ['zh', 'cn', 'chi']:
            return SupportedLanguage.CHINESE
    
    return DEFAULT_LANGUAGE


# Language names for display
LANGUAGE_NAMES = {
    SupportedLanguage.ENGLISH: {
        "en": "English",
        "id": "Bahasa Inggris",
        "jp": "英語",
        "ko": "영어",
        "cn": "英语"
    },
    SupportedLanguage.INDONESIAN: {
        "en": "Indonesian",
        "id": "Bahasa Indonesia",
        "jp": "インドネシア語",
        "ko": "인도네시아어",
        "cn": "印尼语"
    },
    SupportedLanguage.JAPANESE: {
        "en": "Japanese",
        "id": "Bahasa Jepang",
        "jp": "日本語",
        "ko": "일본어",
        "cn": "日语"
    },
    SupportedLanguage.KOREAN: {
        "en": "Korean",
        "id": "Bahasa Korea",
        "jp": "韓国語",
        "ko": "한국어",
        "cn": "韩语"
    },
    SupportedLanguage.CHINESE: {
        "en": "Chinese",
        "id": "Bahasa Mandarin",
        "jp": "中国語",
        "ko": "중국어",
        "cn": "中文"
    }
}
