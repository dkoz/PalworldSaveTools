import sys ,os ,time ,random ,subprocess ,threading ,json 
from import_libs import *
if "--spawn-loader"in sys .argv :
    from PySide6 .QtWidgets import QApplication ,QWidget ,QVBoxLayout ,QFrame ,QLabel ,QGraphicsDropShadowEffect 
    from PySide6 .QtCore import Qt ,QTimer 
    from PySide6 .QtGui import QPixmap ,QColor ,QPainter ,QConicalGradient ,QPen 
    class LoadingOverlay (QWidget ):
        def __init__ (self ,start_time =None ,phrases =None ):
            super ().__init__ ()
            self .setWindowFlags (Qt .Window |Qt .FramelessWindowHint |Qt .WindowStaysOnTopHint |Qt .Tool )
            self .setAttribute (Qt .WA_TranslucentBackground )
            self .setMinimumSize (650 ,565 )
            self .setMaximumSize (650 ,565 )
            self .start_ts =start_time if start_time else time .time ()
            self ._angle =0 
            self .phrases =phrases if phrases else ["LOADING..."]
            self .is_dark_mode =self ._load_theme_pref ()
            self .main_layout =QVBoxLayout (self )
            self .main_layout .setContentsMargins (50 ,50 ,50 ,50 )
            self .container =QFrame ()
            bg_color ="rgba(5, 7, 12, 252)"if self .is_dark_mode else "rgba(245, 245, 245, 252)"
            text_color ="white"if self .is_dark_mode else "#1a1a1a"
            accent_color ="#00f2ff"if self .is_dark_mode else "#005fb8"
            self .container .setStyleSheet (f"background-color: {bg_color }; border-radius: 40px; border: none;")
            self .shadow =QGraphicsDropShadowEffect (self )
            self .shadow .setBlurRadius (40 )
            self .shadow .setXOffset (0 )
            self .shadow .setYOffset (0 )
            self .shadow .setColor (QColor (0 ,0 ,0 ,200 if self .is_dark_mode else 60 ))
            self .container .setGraphicsEffect (self .shadow )
            inner =QVBoxLayout (self .container )
            inner .setContentsMargins (35 ,40 ,35 ,40 )
            inner .setSpacing (20 )
            self .label =QLabel (random .choice (self .phrases ))
            self .label .setAlignment (Qt .AlignCenter )
            self .label .setWordWrap (True )
            self .label .setMinimumHeight (120 )
            self .label .setStyleSheet (f"color: {text_color }; font-family: 'Segoe UI'; font-size: 19px; font-weight: 900; letter-spacing: 1px; background: transparent; border: none;")
            self .icon_label =QLabel ()
            self .icon_label .setAlignment (Qt .AlignCenter )
            self .icon_label .setStyleSheet ("background: transparent; border: none;")
            self .timer_label =QLabel ("00:00.00")
            self .timer_label .setAlignment (Qt .AlignCenter )
            self .timer_label .setStyleSheet (f"color: {accent_color }; font-family: 'Consolas'; font-size: 38px; font-weight: bold; background: transparent; border: none;")
            inner .addWidget (self .label )
            inner .addWidget (self .icon_label )
            inner .addWidget (self .timer_label )
            self .main_layout .addWidget (self .container )
            self .set_icon ()
            self .anim_timer =QTimer (self )
            self .anim_timer .timeout .connect (self .update_sync )
            self .anim_timer .start (10 )
            self .joke_timer =QTimer (self )
            self .joke_timer .timeout .connect (self .cycle_phrase )
            self .joke_timer .start (3500 )
        def _load_theme_pref (self ):
            try :
                if getattr (sys ,'frozen',False ):
                    base =os .path .dirname (sys .executable )
                else :
                    base =os .path .dirname (os .path .abspath (__file__ ))
                paths_to_check =[
                os .path .join (base ,"data","configs","user.cfg"),
                os .path .join (base ,"Assets","data","configs","user.cfg"),
                os .path .join (os .path .dirname (base ),"Assets","data","configs","user.cfg"),
                os .path .join (os .getcwd (),"Assets","data","configs","user.cfg")
                ]
                for cfg_path in paths_to_check :
                    if os .path .exists (cfg_path ):
                        with open (cfg_path ,'r',encoding ='utf-8')as f :
                            data =json .load (f )
                            return data .get ("theme","dark")=="dark"
            except :
                pass 
            return True 
        def cycle_phrase (self ):
            new_phrase =random .choice (self .phrases )
            while new_phrase ==self .label .text ():
                new_phrase =random .choice (self .phrases )
            self .label .setText (new_phrase )
        def update_sync (self ):
            elapsed =time .time ()-self .start_ts 
            self ._angle =(elapsed *300 )%360 
            self .timer_label .setText (f"{int (elapsed //60 ):02d}:{int (elapsed %60 ):02d}.{int ((elapsed *100 )%100 ):02d}")
            self .update ()
        def paintEvent (self ,event ):
            p =QPainter (self )
            p .setRenderHint (QPainter .Antialiasing )
            rect =self .container .geometry ()
            g =QConicalGradient (rect .center (),-self ._angle )
            stops =[(0.0 ,QColor (255 ,0 ,0 )),(0.17 ,QColor (255 ,255 ,0 )),(0.33 ,QColor (0 ,255 ,0 )),(0.5 ,QColor (0 ,255 ,255 )),(0.67 ,QColor (0 ,0 ,255 )),(0.83 ,QColor (255 ,0 ,255 )),(1.0 ,QColor (255 ,0 ,0 ))]
            for s ,c in stops :g .setColorAt (s ,c )
            pen =QPen (g ,10 )
            p .setPen (pen )
            p .drawRoundedRect (rect .adjusted (2 ,2 ,-2 ,-2 ),40 ,40 )
        def set_icon (self ):
            if getattr (sys ,'frozen',False ):
                base =os .path .dirname (sys .executable )
            else :
                base =os .path .dirname (os .path .abspath (__file__ ))
            res_paths =[
            os .path .join (base ,"resources","Xenolord.webp"),
            os .path .join (base ,"Assets","resources","Xenolord.webp"),
            os .path .join (os .path .dirname (base ),"resources","Xenolord.webp"),
            os .path .join (os .path .dirname (base ),"Assets","resources","Xenolord.webp"),
            os .path .join (base ,"..","resources","Xenolord.webp")
            ]
            for path in res_paths :
                if os .path .exists (path ):
                    self .icon_label .setPixmap (QPixmap (path ).scaled (180 ,180 ,Qt .KeepAspectRatio ,Qt .SmoothTransformation ))
                    return 
    app =QApplication (sys .argv )
    st =None 
    passed_phrases =None 
    try :
        idx =sys .argv .index ("--spawn-loader")
        st =float (sys .argv [idx +1 ])
        passed_phrases =json .loads (sys .argv [idx +2 ])
    except :
        pass 
    overlay =LoadingOverlay (start_time =st ,phrases =passed_phrases )
    overlay .show ()
    overlay .move (QApplication .primaryScreen ().geometry ().center ()-overlay .rect ().center ())
    sys .exit (app .exec ())
from PySide6 .QtWidgets import QWidget ,QVBoxLayout ,QFrame ,QLabel ,QApplication ,QMainWindow ,QGraphicsDropShadowEffect 
from PySide6 .QtCore import Qt ,QTimer ,QRectF ,qInstallMessageHandler ,QtMsgType 
from PySide6 .QtGui import QPixmap ,QColor ,QPainter ,QConicalGradient ,QPen 
def qt_suppress_handler (msg_type ,context ,message ):
    if any (err in message for err in ["QProcess: Destroyed","UpdateLayeredWindowIndirect","Unable to set geometry"]):
        return 
    print (message )
qInstallMessageHandler (qt_suppress_handler )
_active_loader_proc =None 
_worker_ref =None 
_result_data ={"status":"idle","data":None }
def run_with_loading (callback ,func ,*args ,**kwargs ):
    global _active_loader_proc ,_worker_ref ,_result_data 
    from PySide6 .QtCore import QTimer 
    _result_data ["status"]="running"
    _result_data ["data"]=None 
    start_time_arg =str (time .time ())
    try :
        loading_phrases =[t (f"loading.phrase.{i }")for i in range (1 ,21 )]
    except :
        loading_phrases =["LOADING..."]
    phrases_arg =json .dumps (loading_phrases )
    if getattr (sys ,'frozen',False ):
        args_list =[sys .executable ,"--spawn-loader",start_time_arg ,phrases_arg ]
    else :
        args_list =[sys .executable ,os .path .abspath (__file__ ),"--spawn-loader",start_time_arg ,phrases_arg ]
    _active_loader_proc =subprocess .Popen (args_list ,creationflags =subprocess .CREATE_NO_WINDOW if os .name =="nt"else 0 )
    def task_wrapper ():
        try :
            _result_data ["data"]=func (*args ,**kwargs )
        except Exception as e :
            _result_data ["data"]=e 
        _result_data ["status"]="finished"
    _worker_ref =threading .Thread (target =task_wrapper ,daemon =True )
    _worker_ref .start ()
    timer =QTimer ()
    timer .setInterval (100 )
    def monitor ():
        global _active_loader_proc 
        if _result_data ["status"]!="finished":
            return 
        timer .stop ()
        if _active_loader_proc :
            _active_loader_proc .terminate ()
            try :
                _active_loader_proc .wait (timeout =1 )
            except subprocess .TimeoutExpired :
                _active_loader_proc .kill ()
            _active_loader_proc =None 
        res =_result_data ["data"]
        _result_data ["status"]="idle"
        if callback :
            callback (res )
    timer .timeout .connect (monitor )
    timer .start ()