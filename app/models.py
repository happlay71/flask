import hashlib
from . import db, login_manager
from datetime import datetime
from flask import current_app, request, url_for
from app.exceptions import ValidationError
from werkzeug.security import generate_password_hash, check_password_hash  # 用于生成密码的散列值，验证密码是否与散列值匹配
from flask_login import UserMixin, AnonymousUserMixin  # 自动提供实现验证用户的功能\检查用户权限
from itsdangerous import URLSafeTimedSerializer as Serializer  # 生成具有时限的令牌
from markdown import markdown
import bleach

# 设置权限常量
class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16

# 模型一般是一个Python类，类=表、类中的属性=表中的列
class Role(db.Model):
    __tablename__ = 'roles'  # 定义在数据库中的表名
    
    id = db.Column(db.Integer, primary_key=True)  # db.Integer为属性/列，primary_key=True定义为True表示列为表的主键
    name = db.Column(db.String(64), unique=True)  # db.String(64)为属性/列，unique=True定义为True表示列不允许重复的值
    users = db.relationship('User', backref='role', lazy='dynamic')  # 建立一对多关系
    # lazy='dynamic' 是指定了关系字段的加载策略为动态加载。这意味着在访问 users 字段时，不会立即加载所有关联的用户对象，而是返回一个查询对象
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

    # 定义Role下的子类继承
    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    # 定义管理权限的方法
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm
    

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm
    

    def reset_permissions(self):
        self.permissions = 0


    def has_permission(self, perm):
        return self.permissions & perm == perm
    
    # 在数据库中创建角色并重置权限
    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()


    def __repr__(self):
        return '<Role %r>' % self.name  # 定义对象的字符串表示形式,以字符串形式输出

# 关联表
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)  # index=True表示在该列上创建索引，以提高查询的性能
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))  # 定义外键
    password_hash = db.Column(db.String(128))  # 用于存储密码的哈希值
    confirmed = db.Column(db.Boolean, default=False)
    
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    avatar_hash = db.Column(db.String(32))  # 使用缓存的MD5散列值生成Gravatar URL
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    # 两个一对多关系实现多对多
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],  # 用于指定外键的字段
                               backref=db.backref('follower', lazy='joined'),  # 用于定义反向引用
                               lazy='dynamic',
                               cascade='all, delete-orphan')  # 删除记录的实体
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')
    
    # 把用户设为自己的关注者
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()

    # 定义默认的用户角色
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = self.gravatar_hash()  # 生成Gravatar URL
        self.follow(self)  # 将自己设置为自己的关注者

    
    @property  # 定义了一个属性方法password，用于获取密码值
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    # 对密码进行哈希处理，并将哈希值存储到 password_hash 属性中
    @password.setter  # 定义了password的设置器，用于设置密码
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # 用于验证输入的密码是否与存储的密码哈希值匹配
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # 1.生成令牌，有效期一小时--验证电子邮件
    # 会显示返回值无法解码成字符串，需将config.py里的secret_ky编码为字节形式!!!
    def generate_confirmation_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'confirm': self.id})
    
    # 检验令牌和对应Id
    def confirm(self, token, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'), max_age=expiration)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True
    
    # 重设密码
    def generate_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'reset': self.id})
    

    @staticmethod
    def reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    # 修改电子邮件
    def generate_email_change_token(self, new_email):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps(
            {'change_email': self.id, 'new_email': new_email})


    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        return True
    
    # 检查用户是否有指定权限
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)
    

    def is_administrator(self):
        return self.can(Permission.ADMIN)
    
    # 刷新用户最后访问时间
    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    # 生成Gravatar URL
    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()  # 生成了用户邮箱的 MD5 哈希值

    # 生成头像
    def gravatar(self, size=100, default='identicon', rating='g'):  # rating='g': 头像评级参数
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()  
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)
    
    # 关注关系的辅助方法
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)
    

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)
    

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(
            followed_id=user.id).first() is not None
    

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None
    
    # 联结操作-获取关注用户的文章
    @property  # 将方法转换为只读属性，可直接用user.xxx方法调用
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

    # 2.生成令牌--验证用户登录信息
    def generate_auth_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps({'id': self.id})
    

    @staticmethod  # 定义静态方法的装饰器
    def verify_auth_token(token, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'), max_age=expiration)  # 接收一个令牌，并将该该令牌转换为原始数据
        except:
            return None
        return User.query.get(data['id'])
    
    # 把用户转换成JSON格式的序列化字典
    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts_url': url_for('api.get_user_posts', id=self.id),
            'followed_posts_url':url_for('api.get_user_followed_posts',
                                         id=self.id),
            'post_count': self.posts.count(),
        }
        return json_user


    def __repr__(self):
        return '<User %r>' % self.username
    
#匿名用户，没有权限
class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False
    

    def is_administrator(self):
        return False
    

login_manager.anonymous_user = AnonymousUser
    
# 获取用户对象
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    # 在服务端处理富文本
    # target 表示目标对象（通常是该类的实例），value 表示 body 属性的新值，oldvalue 表示 body 属性的旧值，initiator 表示触发属性变化的事件
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))  # strip表示要去除 HTML 中的所有空白字符，包括换行符、空格等
        
    # 把文章转化为JSON格式的序列化字典
    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
            'comments_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments.count()
        }
        return json_post
    
    # 从JSON格式数据创建一篇博客文章
    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)
        
# 监听的模型属性、要监听的事件类型和回调函数
db.event.listen(Post.body, 'set', Post.on_changed_body)


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))


    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                        'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))
        

    def to_json(self):
        json_comment = {
            'url': url_for('api.get_comment', id=self.id),
            'post_url': url_for('api.get_post', id=self.post_id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id)
        }
        return json_comment
    

    @staticmethod
    def from_json(json_comment):
        body = json_comment.get('body')
        if body is None or body == '':
            raise ValidationError('comment does not have a body')
        return Comment(body=body)


db.event.listen(Comment.body, 'set', Comment.on_changed_body)



