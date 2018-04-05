from . import views
from online_classes.views import MainView,StaticPageView,LoginView,SingleProductView, AdminView, AllProductsView, LoginView, ImageView, UserProfileView, AddToCartView, CheckoutView, CommentsView, DemoClassView, ProfileImageView, UnixTerminalView, MessagesView, ConversationView, ProfileView, AuthView
from django.conf.urls import patterns, url
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    url(r'^page-login.*', LoginView.as_view()),
    url(r'^index.*', MainView.as_view()),
    url(r'^class.*', SingleProductView.as_view()),
    url(r'^product.*', AllProductsView.as_view()),
    url(r'^admin', AdminView.as_view()),
    url(r'^login', LoginView.as_view()),
    url(r'^ckImage', ImageView.as_view()),
    url(r'^user-profile', UserProfileView.as_view()),
    url(r'^add-to-cart', AddToCartView.as_view()),
    url(r'^checkout', CheckoutView.as_view()),
    url(r'^comments', CommentsView.as_view()),
    url(r'^bookdemo', DemoClassView.as_view()),
    url(r'^image', ProfileImageView.as_view()),
    url(r'^unix-terminal', UnixTerminalView.as_view()),
    url(r'^messages', MessagesView.as_view()),
    url(r'^conversation', ConversationView.as_view()),
    url(r'^profile', ProfileView.as_view()),
    url(r'^auth', AuthView.as_view()),
    url(r'media/(?P<path>.*)', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    url(r'.+', StaticPageView.as_view()),
    url(r'', MainView.as_view()),
]
