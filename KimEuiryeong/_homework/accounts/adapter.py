from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.text import slugify
from django.contrib.auth import get_user_model
import uuid

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """
        소셜 로그인으로 사용자를 저장하기 전에 호출됩니다.
        """
        user = sociallogin.user
        
        # 1. 고유한 username 생성 (기존 로직 유지)
        if not user.username or user.username == '' or self.is_existing_username(user.username):
            if user.email:
                username_base = slugify(user.email.split('@')[0])
            else:
                username_base = uuid.uuid4().hex[:8]

            username = username_base
            i = 1
            while self.is_existing_username(username):
                username = f"{username_base}{i}"
                i += 1
            user.username = username

        # 2. 소셜 서비스 제공자별로 추가 정보 채우기
        self.populate_user_fields(user, sociallogin)
        
        # 3. 최종 사용자 정보 저장
        super().save_user(request, sociallogin, form)
        user.save() # populate_user_fields에서 변경된 내용을 확실히 저장
        return user

    def populate_user_fields(self, user, sociallogin):
        """
        sociallogin 객체에서 추가 정보를 추출하여 user 모델의 필드를 채웁니다.
        """
        extra_data = sociallogin.account.extra_data
        
        # --- 이름(name) 필드 채우기 ---
        if sociallogin.account.provider == 'naver':
            naver_data = extra_data.get('response', {})
            user.name = naver_data.get('name', '')
        
        elif sociallogin.account.provider == 'kakao':
            kakao_account = extra_data.get('kakao_account', {})
            user.name = kakao_account.get('name', '')

        # --- 닉네임(nickname) 필드 채우기 (공통 로직) ---
        user.nickname = self.generate_unique_nickname(user.email, user.username)

    def generate_unique_nickname(self, email, username):
        """이메일 또는 username을 기반으로 고유한 닉네임을 생성합니다."""
        if email:
            base_nickname = slugify(email.split('@')[0])
        else:
            base_nickname = username # 이메일이 없는 경우 username을 기반으로 생성

        nickname = base_nickname
        i = 1
        # is_existing_nickname 헬퍼를 사용해 중복을 확인하고, 중복 시 숫자를 붙입니다.
        while self.is_existing_nickname(nickname):
            nickname = f"{base_nickname}{i}"
            i += 1
        return nickname

    def is_existing_username(self, username):
        """주어진 username이 이미 존재하는지 확인합니다."""
        User = get_user_model()
        return User.objects.filter(username=username).exists()

    def is_existing_nickname(self, nickname):
        """주어진 nickname이 이미 존재하는지 확인합니다."""
        User = get_user_model()
        return User.objects.filter(nickname=nickname).exists()