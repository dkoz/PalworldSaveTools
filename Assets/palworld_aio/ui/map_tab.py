import os 
import json 
import math 
import random 
from PySide6 .QtWidgets import (
QWidget ,QVBoxLayout ,QHBoxLayout ,QGraphicsView ,QGraphicsScene ,
QGraphicsPixmapItem ,QGraphicsEllipseItem ,QMenu ,QLineEdit ,
QTreeWidget ,QTreeWidgetItem ,QSplitter ,QLabel ,QMessageBox ,
QFileDialog ,QInputDialog ,QGraphicsItem ,QGraphicsObject 
)
from PySide6 .QtCore import Qt ,QRectF ,QPointF ,QPoint ,Signal ,QTimer ,QPropertyAnimation ,QEasingCurve ,Property ,QParallelAnimationGroup 
from PySide6 .QtGui import (
QPixmap ,QPen ,QBrush ,QColor ,QPainter ,QTransform ,
QRadialGradient ,QFont ,QCursor 
)
from i18n import t 
import palworld_coord 
try :
    from palworld_aio import constants 
    from palworld_aio .data_manager import delete_base_camp ,get_tick 
    from palworld_aio .base_manager import export_base_json ,import_base_json 
    from palworld_aio .guild_manager import rename_guild 
    from palworld_aio .widgets import BaseHoverOverlay 
except ImportError :
    from ..import constants 
    from ..data_manager import delete_base_camp ,get_tick 
    from ..base_manager import export_base_json ,import_base_json 
    from ..guild_manager import rename_guild 
    from ..widgets import BaseHoverOverlay 
class BaseMarker (QGraphicsPixmapItem ):
    def __init__ (self ,base_data ,x ,y ,base_icon_pixmap ,config ):
        super ().__init__ ()
        self .base_data =base_data 
        self .config =config 
        self .base_icon_original =base_icon_pixmap 
        self .marker_type =config ['marker']['type']
        if self .marker_type =='dot':
            self .current_size =config ['marker']['dot']['size']
            if not config ['marker']['dot']['dynamic_sizing']:
                self .setFlag (QGraphicsItem .ItemIgnoresTransformations ,True )
        else :
            self .current_size =config ['marker']['icon']['base_size']
            if not config ['marker']['icon']['dynamic_sizing']:
                self .setFlag (QGraphicsItem .ItemIgnoresTransformations ,True )
        self ._update_icon_size (self .current_size )
        self .center_x =x 
        self .center_y =y 
        self .setPos (x ,y )
        self .setFlag (QGraphicsItem .ItemIsSelectable ,True )
        self .setAcceptHoverEvents (True )
        self .glow_alpha =0 
        self .glow_increasing =True 
        self .is_hovered =False 
        self .shine_pos =0 
    def _update_icon_size (self ,size ):
        self .current_size =size 
        scaled =self .base_icon_original .scaled (
        int (size ),int (size ),
        Qt .KeepAspectRatio ,
        Qt .SmoothTransformation 
        )
        self .scaled_pixmap =scaled 
        self .setPixmap (scaled )
        self .setOffset (-size /2 ,-size /2 )
    def scale_to_zoom (self ,zoom_level ):
        if self .marker_type =='dot':
            if not self .config ['marker']['dot']['dynamic_sizing']:
                return 
            size_min =self .config ['marker']['dot']['size_min']
            size_max =self .config ['marker']['dot']['size_max']
            formula =self .config ['marker']['dot']['dynamic_sizing_formula']
        else :
            if not self .config ['marker']['icon']['dynamic_sizing']:
                return 
            size_min =self .config ['marker']['icon']['size_min']
            size_max =self .config ['marker']['icon']['size_max']
            formula =self .config ['marker']['icon']['dynamic_sizing_formula']
        clamped_zoom =max (0.05 ,min (zoom_level ,10.0 ))
        if formula =='sqrt':
            raw_size =25 /math .sqrt (clamped_zoom )
        elif formula =='linear':
            raw_size =100 -(zoom_level *10 )
        elif formula =='log':
            raw_size =50 /math .log (clamped_zoom +1 )
        else :
            raw_size =self .current_size 
        new_size =max (size_min ,min (size_max ,int (raw_size )))
        if new_size !=self .current_size :
            self ._update_icon_size (new_size )
    def paint (self ,painter ,option ,widget =None ):
        painter .setRenderHint (QPainter .Antialiasing )
        painter .setRenderHint (QPainter .SmoothPixmapTransform )
        if self .marker_type =='icon':
            shine_pixmap =self .scaled_pixmap .copy ()
            mask_pixmap =QPixmap (self .current_size ,self .current_size )
            mask_pixmap .fill (QColor (0 ,0 ,0 ,0 ))
            mask_painter =QPainter (mask_pixmap )
            mask_painter .setPen (Qt .NoPen )
            mask_painter .setBrush (QColor (255 ,255 ,255 ,120 ))
            shine_pos =self .shine_pos -50 
            points =[
            QPointF (shine_pos ,0 ),
            QPointF (shine_pos +15 ,0 ),
            QPointF (shine_pos -5 ,self .current_size ),
            QPointF (shine_pos -20 ,self .current_size )
            ]
            mask_painter .drawPolygon (points )
            mask_painter .setCompositionMode (QPainter .CompositionMode_DestinationIn )
            mask_painter .drawPixmap (0 ,0 ,self .scaled_pixmap )
            mask_painter .end ()
            shine_painter =QPainter (shine_pixmap )
            shine_painter .setCompositionMode (QPainter .CompositionMode_Plus )
            shine_painter .drawPixmap (0 ,0 ,mask_pixmap )
            shine_painter .end ()
            self .setPixmap (shine_pixmap )
        glow_config =self .config ['glow']
        if glow_config ['enabled']and (self .isSelected ()or self .glow_alpha >0 or self .is_hovered ):
            alpha =max (self .glow_alpha ,glow_config ['hover_alpha']if self .is_hovered else 0 )
            glow_radius =self .current_size *glow_config ['radius_multiplier']
            glow_color =QColor (*glow_config ['color'])
            gradient =QRadialGradient (0 ,0 ,glow_radius )
            gradient .setColorAt (0 ,QColor (glow_color .red (),glow_color .green (),glow_color .blue (),alpha ))
            gradient .setColorAt (0.5 ,QColor (glow_color .red (),glow_color .green (),glow_color .blue (),alpha //2 ))
            gradient .setColorAt (1 ,QColor (glow_color .red (),glow_color .green (),glow_color .blue (),0 ))
            painter .setBrush (gradient )
            painter .setPen (Qt .NoPen )
            painter .drawEllipse (
            QRectF (
            -glow_radius ,
            -glow_radius ,
            glow_radius *2 ,
            glow_radius *2 
            )
            )
        super ().paint (painter ,option ,widget )
    def hoverEnterEvent (self ,event ):
        self .is_hovered =True 
        self .update ()
    def hoverLeaveEvent (self ,event ):
        self .is_hovered =False 
        self .update ()
    def start_glow (self ):
        self .glow_alpha =180 
    def update_glow (self ):
        glow_config =self .config ['glow']
        alpha_min =glow_config ['selected_alpha_min']
        alpha_max =glow_config ['selected_alpha_max']
        speed =glow_config ['animation_speed']
        if self .isSelected ():
            if self .glow_increasing :
                self .glow_alpha +=speed 
                if self .glow_alpha >=alpha_max :
                    self .glow_increasing =False 
            else :
                self .glow_alpha -=speed 
                if self .glow_alpha <=alpha_min :
                    self .glow_increasing =True 
        else :
            if self .glow_alpha >0 :
                self .glow_alpha -=speed *1.5 
                if self .glow_alpha <0 :
                    self .glow_alpha =0 
        self .shine_pos =(self .shine_pos +2 )%100 
        self .update ()
class EffectItem (QGraphicsObject ):
    def __init__ (self ,x ,y ,duration =1000 ):
        super ().__init__ ()
        self .center_x =x 
        self .center_y =y 
        self .duration =duration 
        self ._progress =0.0 
        self .setPos (x ,y )
    @Property (float )
    def progress (self ):
        return self ._progress 
    @progress .setter 
    def progress (self ,value ):
        self ._progress =value 
        self .update ()
    def boundingRect (self ):
        return QRectF (-200 ,-200 ,400 ,400 )
class DeleteEffect (EffectItem ):
    def paint (self ,painter ,option ,widget =None ):
        painter .setRenderHint (QPainter .Antialiasing )
        radius =self ._progress *150 
        alpha =int (255 *(1 -self ._progress ))
        painter .setPen (QPen (QColor (255 ,80 ,80 ,alpha ),5 ))
        painter .setBrush (Qt .NoBrush )
        painter .drawEllipse (QPointF (0 ,0 ),radius ,radius )
        if radius >30 :
            painter .setPen (QPen (QColor (255 ,150 ,0 ,alpha ),3 ))
            painter .drawEllipse (QPointF (0 ,0 ),radius -30 ,radius -30 )
        if self ._progress <0.3 :
            flash_alpha =int (200 *(1 -self ._progress /0.3 ))
            painter .setBrush (QColor (255 ,200 ,0 ,flash_alpha ))
            painter .setPen (Qt .NoPen )
            painter .drawEllipse (QPointF (0 ,0 ),40 ,40 )
class ImportEffect (EffectItem ):
    def paint (self ,painter ,option ,widget =None ):
        painter .setRenderHint (QPainter .Antialiasing )
        for i in range (3 ):
            phase =(self ._progress +i *0.33 )%1.0 
            radius =phase *100 
            alpha =int (180 *(1 -phase ))
            painter .setPen (QPen (QColor (0 ,255 ,150 ,alpha ),3 ))
            painter .setBrush (Qt .NoBrush )
            painter .drawEllipse (QPointF (0 ,0 ),radius ,radius )
        if self ._progress <0.7 :
            painter .setBrush (QColor (100 ,255 ,200 ,int (255 *(1 -self ._progress ))))
            painter .setPen (Qt .NoPen )
            for angle in range (0 ,360 ,45 ):
                rad =math .radians (angle )
                dist =60 +self ._progress *40 
                x =math .cos (rad )*dist 
                y =math .sin (rad )*dist 
                size =8 -self ._progress *6 
                painter .drawEllipse (QPointF (x ,y ),size ,size )
class ExportEffect (EffectItem ):
    def paint (self ,painter ,option ,widget =None ):
        painter .setRenderHint (QPainter .Antialiasing )
        beam_height =self ._progress *200 
        alpha =int (200 *(1 -self ._progress ))
        gradient =QRadialGradient (0 ,-beam_height /2 ,30 )
        gradient .setColorAt (0 ,QColor (100 ,200 ,255 ,alpha ))
        gradient .setColorAt (1 ,QColor (100 ,200 ,255 ,0 ))
        painter .setBrush (gradient )
        painter .setPen (Qt .NoPen )
        painter .drawRect (QRectF (-20 ,-beam_height ,40 ,beam_height ))
        for i in range (5 ):
            particle_y =-(i *40 +self ._progress *150 )%200 
            particle_alpha =int (alpha *(1 -abs (particle_y )/200 ))
            painter .setBrush (QColor (150 ,220 ,255 ,particle_alpha ))
            painter .drawEllipse (QPointF (random .randint (-15 ,15 ),particle_y ),4 ,4 )
class MapGraphicsView (QGraphicsView ):
    marker_clicked =Signal (object )
    marker_double_clicked =Signal (object )
    marker_right_clicked =Signal (object ,QPointF )
    marker_hover_entered =Signal (object ,QPointF )
    marker_hover_left =Signal ()
    zoom_changed =Signal (float )
    def __init__ (self ,config ):
        super ().__init__ ()
        self .config =config 
        self .setRenderHint (QPainter .Antialiasing )
        self .setRenderHint (QPainter .SmoothPixmapTransform )
        self .setBackgroundBrush (Qt .transparent )
        self .setDragMode (QGraphicsView .ScrollHandDrag )
        self .setTransformationAnchor (QGraphicsView .AnchorUnderMouse )
        self .setResizeAnchor (QGraphicsView .AnchorUnderMouse )
        self .setVerticalScrollBarPolicy (Qt .ScrollBarAlwaysOff )
        self .setHorizontalScrollBarPolicy (Qt .ScrollBarAlwaysOff )
        self .setMouseTracking (True )
        self ._hovered_marker =None 
        zoom_config =self .config ['zoom']
        self .zoom_factor =zoom_config ['factor']
        self .current_zoom =1.0 
        self .min_zoom =zoom_config ['min']
        self .max_zoom =zoom_config ['max']
        self .zoom_timer =QTimer ()
        self .zoom_timer .timeout .connect (self ._smooth_zoom_step )
        self .target_zoom =1.0 
        self .target_center =None 
        self .is_animating =False 
        self .coords_label =QLabel (f"{t ('cursor_coords')if t else 'Cursor'}: 0, 0",self )
        self .coords_label .setStyleSheet ("background-color: rgba(0, 0, 0, 150); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; min-width: 120px;")
        self .coords_label .move (10 ,self .height ()-30 )
        self .coords_label .setVisible (False )
        self .zoom_label =QLabel ("Zoom: 100%",self )
        self .zoom_label .setStyleSheet ("background-color: rgba(0, 0, 0, 150); color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; min-width: 80px;")
        self .zoom_label .move (self .width ()-90 ,self .height ()-30 )
        self .zoom_label .setAlignment (Qt .AlignCenter )
    def wheelEvent (self ,event ):
        zoom_in =event .angleDelta ().y ()>0
        if zoom_in :
            factor =self .zoom_factor
            self .current_zoom *=factor
        else :
            factor =1 /self .zoom_factor
            self .current_zoom *=factor
        if self .current_zoom <self .min_zoom :
            factor =self .min_zoom /(self .current_zoom /factor )
            self .current_zoom =self .min_zoom
        elif self .current_zoom >self .max_zoom :
            factor =self .max_zoom /(self .current_zoom /factor )
            self .current_zoom =self .max_zoom
        self .scale (factor ,factor )
        self .zoom_label .setText (f"Zoom: {int (self .current_zoom *100 )}%")
        self .zoom_changed .emit (self .current_zoom )
    def mousePressEvent (self ,event ):
        item =self .itemAt (event .pos ())
        if isinstance (item ,BaseMarker ):
            if event .button ()==Qt .LeftButton :
                self .scene ().clearSelection ()
                item .setSelected (True )
                item .start_glow ()
                self .marker_clicked .emit (item .base_data )
            elif event .button ()==Qt .RightButton :
                self .marker_right_clicked .emit (item .base_data ,event .globalPosition ())
                return 
        else :
            if event .button ()==Qt .LeftButton :
                self .scene ().clearSelection ()
        super ().mousePressEvent (event )
    def mouseDoubleClickEvent (self ,event ):
        item =self .itemAt (event .pos ())
        if isinstance (item ,BaseMarker ):
            if event .button ()==Qt .LeftButton :
                self .marker_double_clicked .emit (item .base_data )
                zoom_level =self .config ['zoom']['double_click_target']
                self .animate_to_marker (item ,zoom_level =zoom_level )
                return 
        super ().mouseDoubleClickEvent (event )
    def mouseMoveEvent (self ,event ):
        item =self .itemAt (event .pos ())
        if isinstance (item ,BaseMarker ):
            if self ._hovered_marker !=item :
                if self ._hovered_marker is not None :
                    self .marker_hover_left .emit ()
                self ._hovered_marker =item 
                global_pos =self .mapToGlobal (event .pos ())
                self .marker_hover_entered .emit (item .base_data ,QPointF (global_pos .x (),global_pos .y ()))
        else :
            if self ._hovered_marker is not None :
                self ._hovered_marker =None 
                self .marker_hover_left .emit ()
        scene_pos =self .mapToScene (event .pos ())
        if self .scene ()and self .scene ().sceneRect ().contains (scene_pos ):
            rect =self .scene ().sceneRect ()
            width ,height =rect .width (),rect .height ()
            img_x ,img_y =scene_pos .x (),scene_pos .y ()
            x_world =(img_x /width )*2000 -1000 
            y_world =1000 -(img_y /height )*2000 
            # Convert to Old coordinates for display
            save_x ,save_y =palworld_coord .map_to_sav (x_world ,y_world ,new =True )
            old_x ,old_y =palworld_coord .sav_to_map (save_x ,save_y ,new =False )
            self .coords_label .setText (f"{t ('cursor_coords')if t else 'Cursor'}: {int (old_x )}, {int (old_y )}")
            self .coords_label .setVisible (True )
        else :
            self .coords_label .setVisible (False )
        super ().mouseMoveEvent (event )
    def leaveEvent (self ,event ):
        if self ._hovered_marker is not None :
            self ._hovered_marker =None 
            self .marker_hover_left .emit ()
        self .coords_label .setVisible (False )
        super ().leaveEvent (event )
    def animate_to_marker (self ,marker ,zoom_level =None ):
        if zoom_level is None :
            zoom_level =self .config ['zoom']['double_click_target']
        self .target_zoom =zoom_level 
        self .target_center =QPointF (marker .center_x ,marker .center_y )
        self .resetTransform ()
        self .current_zoom =1.0 
        self .centerOn (self .target_center )
        self .is_animating =True 
        fps =self .config ['zoom']['animation_fps']
        interval =int (1000 /fps )
        if not self .zoom_timer .isActive ():
            self .zoom_timer .start (interval )
    def _smooth_zoom_step (self ):
        if not self .is_animating :
            self .zoom_timer .stop ()
            return
        if self .target_center :
            self .centerOn (self .target_center )
        zoom_diff =self .target_zoom -self .current_zoom
        if abs (zoom_diff )<0.05 :
            factor =self .target_zoom /self .current_zoom
            self .scale (factor ,factor )
            self .current_zoom =self .target_zoom
            self .centerOn (self .target_center )
            self .is_animating =False
            self .zoom_timer .stop ()
            self .zoom_label .setText (f"Zoom: {int (self .current_zoom *100 )}%")
            self .zoom_changed .emit (self .current_zoom )
            return
        easing_factor =self .config ['zoom']['animation_speed']
        zoom_step =zoom_diff *easing_factor
        factor =(self .current_zoom +zoom_step )/self .current_zoom
        self .current_zoom +=zoom_step
        self .scale (factor ,factor )
        self .zoom_label .setText (f"Zoom: {int (self .current_zoom *100 )}%")
        self .zoom_changed .emit (self .current_zoom )
    def resizeEvent (self ,event ):
        super ().resizeEvent (event )
        self .coords_label .move (10 ,self .height ()-30 )
        self .zoom_label .move (self .width ()-90 ,self .height ()-30 )
    def reset_view (self ):
        self .resetTransform ()
        self .current_zoom =1.0 
        if self .scene ():
            self .fitInView (self .scene ().sceneRect (),Qt .KeepAspectRatio )
            if self .scene ().sceneRect ().width ()>0 :
                self .current_zoom =self .viewport ().width ()/self .scene ().sceneRect ().width ()
        self .zoom_changed .emit (self .current_zoom )
class MapTab (QWidget ):
    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .parent_window =parent 
        self .guilds_data ={}
        self .filtered_guilds ={}
        self .base_markers =[]
        self .active_effects =[]
        self .search_text =""
        self ._map_widget =None 
        self ._splitter =None 
        self ._sidebar_widget =None 
        self ._load_config ()
        self .map_width =2048 
        self .map_height =2048 
        self ._load_base_icon ()
        self ._setup_ui ()
        self ._setup_animation ()
    def _load_config (self ):
        base_dir =os .path .dirname (os .path .dirname (os .path .dirname (os .path .abspath (__file__ ))))
        config_path =os .path .join (base_dir ,'data','configs','map_viewer.json')
        default_config ={
        "marker":{
        "type":"icon",
        "dot":{
        "size":24 ,"color":[255 ,0 ,0 ],"border_width":3 ,
        "border_color":[180 ,0 ,0 ],"size_min":24 ,"size_max":24 ,
        "dynamic_sizing":False ,"dynamic_sizing_formula":"sqrt"
        },
        "icon":{
        "path":"resources/baseicon.png","size_min":28 ,"size_max":28 ,
        "base_size":28 ,"dynamic_sizing":False ,"dynamic_sizing_formula":"sqrt"
        }
        },
        "glow":{
        "enabled":True ,"color":[59 ,142 ,208 ],
        "selected_alpha_min":80 ,"selected_alpha_max":180 ,
        "animation_speed":8 ,"hover_alpha":80 ,"radius_multiplier":1.5 
        },
        "zoom":{
        "factor":1.15 ,"min":0.1 ,"max":20.0 ,
        "double_click_target":2.5 ,"animation_speed":0.2 ,"animation_fps":60 
        },
        "effects":{
        "delete":{"enabled":True ,"duration":1000 ,"max_radius":150 ,
        "colors":{"outer":[255 ,80 ,80 ],"inner":[255 ,150 ,0 ],"flash":[255 ,200 ,0 ]}},
        "import":{"enabled":True ,"duration":1000 ,"pulse_count":3 ,
        "color":[0 ,255 ,150 ],"sparkle_color":[100 ,255 ,200 ]},
        "export":{"enabled":True ,"duration":1000 ,"color":[100 ,200 ,255 ]}
        }
        }
        if os .path .exists (config_path ):
            try :
                import json 
                with open (config_path ,'r',encoding ='utf-8')as f :
                    user_config =json .load (f )
                self .config =self ._merge_config (default_config ,user_config )
            except Exception as e :
                print (f"Error loading map_viewer.json: {e }, using defaults")
                self .config =default_config 
        else :
            self .config =default_config 
        return self .config 
    def _merge_config (self ,default ,user ):
        result =default .copy ()
        for key ,value in user .items ():
            if key in result and isinstance (result [key ],dict )and isinstance (value ,dict ):
                result [key ]=self ._merge_config (result [key ],value )
            else :
                result [key ]=value 
        return result 
    def _create_dot_pixmap (self ,size ):
        from PySide6 .QtGui import QPainter ,QPen ,QBrush 
        from PySide6 .QtCore import QRectF 
        dot_config =self .config ['marker']['dot']
        pixmap =QPixmap (size ,size )
        pixmap .fill (QColor (0 ,0 ,0 ,0 ))
        painter =QPainter (pixmap )
        painter .setRenderHint (QPainter .Antialiasing )
        if dot_config ['border_width']>0 :
            painter .setPen (QPen (QColor (*dot_config ['border_color']),dot_config ['border_width']))
        else :
            painter .setPen (Qt .NoPen )
        painter .setBrush (QBrush (QColor (*dot_config ['color'])))
        border_offset =dot_config ['border_width']/2 
        painter .drawEllipse (QRectF (border_offset ,border_offset ,
        size -dot_config ['border_width'],
        size -dot_config ['border_width']))
        painter .end ()
        return pixmap 
    def _load_base_icon (self ):
        base_dir =os .path .dirname (os .path .dirname (os .path .dirname (os .path .abspath (__file__ ))))
        icon_path_config =self .config ['marker']['icon']['path']
        icon_path =os .path .join (base_dir ,icon_path_config )
        if os .path .exists (icon_path ):
            self .base_icon_pixmap =QPixmap (icon_path )
        else :
            alt_icon_path =os .path .join (base_dir ,'Assets','resources','baseicon.png')
            if os .path .exists (alt_icon_path ):
                self .base_icon_pixmap =QPixmap (alt_icon_path )
            else :
                self .base_icon_pixmap =self ._create_dot_pixmap (32 )
    def _setup_ui (self ):
        layout =QHBoxLayout (self )
        layout .setContentsMargins (0 ,0 ,0 ,0 )
        splitter =QSplitter (Qt .Horizontal )
        self ._map_widget =QWidget ()
        map_layout =QVBoxLayout (self ._map_widget )
        map_layout .setContentsMargins (0 ,0 ,0 ,0 )
        self .view =MapGraphicsView (self .config )
        self .scene =QGraphicsScene ()
        self .view .setScene (self .scene )
        self .view .marker_clicked .connect (self ._on_marker_clicked )
        self .view .marker_double_clicked .connect (self ._on_marker_double_clicked )
        self .view .marker_right_clicked .connect (self ._on_marker_right_clicked )
        self .view .zoom_changed .connect (self ._on_zoom_changed )
        self .hover_overlay =BaseHoverOverlay ()
        self .view .marker_hover_entered .connect (self ._on_marker_hover_enter )
        self .view .marker_hover_left .connect (self ._on_marker_hover_leave )
        self ._load_map ()
        map_layout .addWidget (self .view )
        self ._sidebar_widget =QWidget ()
        sidebar_layout =QVBoxLayout (self ._sidebar_widget )
        self .search_input =QLineEdit ()
        self .search_input .setObjectName ("searchInput")
        self .search_input .setPlaceholderText (t ('map.search.placeholder')if t else 'Search guilds, leaders, bases...')
        self .search_input .textChanged .connect (self ._on_search_changed )
        sidebar_layout .addWidget (self .search_input )
        self .guild_tree =QTreeWidget ()
        self .guild_tree .setObjectName ("searchTree")
        self .guild_tree .setHeaderLabels ([
        t ('map.header.guild')if t else 'Guild',
        t ('map.header.leader')if t else 'Leader',
        t ('map.header.lastseen')if t else 'Last Seen',
        t ('map.header.bases')if t else 'Bases'
        ])
        self .guild_tree .setColumnWidth (0 ,120 )
        self .guild_tree .setColumnWidth (1 ,110 )
        self .guild_tree .setColumnWidth (2 ,90 )
        self .guild_tree .setColumnWidth (3 ,60 )
        self .guild_tree .itemExpanded .connect (self ._on_item_expanded )
        self .guild_tree .itemClicked .connect (self ._on_tree_item_clicked )
        self .guild_tree .itemDoubleClicked .connect (self ._on_tree_item_double_clicked )
        self .guild_tree .setContextMenuPolicy (Qt .CustomContextMenu )
        self .guild_tree .customContextMenuRequested .connect (self ._on_tree_context_menu )
        sidebar_layout .addWidget (self .guild_tree )
        self .info_label =QLabel (t ('map.info.select_base')if t else 'Click on a base marker or list item to view details')
        self .info_label .setWordWrap (True )
        self .info_label .setStyleSheet ("padding: 10px; background-color: rgba(0, 180, 255, 30); border-radius: 4px;")
        sidebar_layout .addWidget (self .info_label )
        self ._splitter =splitter 
        splitter .addWidget (self ._map_widget )
        splitter .addWidget (self ._sidebar_widget )
        splitter .setSizes ([850 ,550 ])
        layout .addWidget (splitter )
        QTimer .singleShot (100 ,self ._fix_initial_layout )
    def _fix_initial_layout (self ):
        if self ._splitter :
            self ._splitter .setSizes ([850 ,550 ])
            self ._splitter .updateGeometry ()
            self .updateGeometry ()
            if self .scene :
                self .view .fitInView (self .scene .sceneRect (),Qt .KeepAspectRatio )
    def _on_marker_hover_enter (self ,base_data ,global_pos ):
        self .hover_overlay .show_for_base (base_data ,QPoint (int (global_pos .x ()),int (global_pos .y ())))
    def _on_marker_hover_leave (self ):
        self .hover_overlay .hide_overlay ()
    def _load_map (self ):
        base_dir =os .path .dirname (os .path .dirname (os .path .dirname (os .path .abspath (__file__ ))))
        map_path =os .path .join (base_dir ,'resources','worldmap.png')
        if os .path .exists (map_path ):
            pixmap =QPixmap (map_path )
        else :
            pixmap =QPixmap (2048 ,2048 )
            pixmap .fill (QColor (30 ,30 ,30 ))
        self .map_width =pixmap .width ()
        self .map_height =pixmap .height ()
        self .map_item =QGraphicsPixmapItem (pixmap )
        self .scene .addItem (self .map_item )
        self .scene .setSceneRect (self .map_item .boundingRect ())
        if self .map_width >0 and self .map_height >0 :
            self .view .fitInView (self .scene .sceneRect (),Qt .KeepAspectRatio )
            viewport =self .view .viewport ()
            self .view .current_zoom =self .view .viewport ().width ()/self .map_width
            self .view .zoom_label .setText (f"Zoom: {int (self .view .current_zoom *100 )}%")
            self .view .zoom_changed .emit (self .view .current_zoom )
    def _setup_animation (self ):
        self .anim_timer =QTimer (self )
        self .anim_timer .timeout .connect (self ._update_animations )
        self .anim_timer .start (50 )
    def _update_animations (self ):
        for marker in self .base_markers :
            marker .update_glow ()
    def refresh (self ):
        if not constants .loaded_level_json :
            return 
        self .guilds_data =self ._get_guild_bases ()
        self .filtered_guilds =self .guilds_data 
        self ._update_markers ()
        self ._update_tree ()
    def _get_guild_bases (self ):
        guilds ={}
        try :
            wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
            group_map =wsd .get ('GroupSaveDataMap',{}).get ('value',[])
            base_map ={
            str (b ['key']).replace ('-',''):b ['value']
            for b in wsd .get ('BaseCampSaveData',{}).get ('value',[])
            }
            tick =get_tick ()
            for entry in group_map :
                try :
                    if entry ['value']['GroupType']['value']['value']!='EPalGroupType::Guild':
                        continue 
                except :
                    continue 
                gid =str (entry ['key'])
                g_val =entry ['value']
                admin_uid =str (g_val ['RawData']['value'].get ('admin_player_uid',''))
                leader_name =None 
                for p in g_val ['RawData']['value'].get ('players',[]):
                    if str (p .get ('player_uid',''))==admin_uid :
                        leader_name =p .get ('player_info',{}).get ('player_name',admin_uid )
                        break 
                if not leader_name :
                    leader_name =admin_uid if admin_uid else (t ('map.unknown.leader')if t else 'Unknown')
                if leader_name ==(t ('map.unknown.leader')if t else 'Unknown'):
                    continue 
                times =[
                p .get ('player_info',{}).get ('last_online_real_time')
                for p in g_val ['RawData']['value'].get ('players',[])
                if p .get ('player_info',{}).get ('last_online_real_time')
                ]
                if times :
                    diff =(tick -max (times ))/10000000.0 
                    days =int (diff //86400 )
                    hours =int (diff %86400 //3600 )
                    mins =int (diff %3600 //60 )
                    if days >0 :
                        last_seen =f'{days }d {hours }h'
                    elif hours >0 :
                        last_seen =f'{hours }h {mins }m'
                    else :
                        last_seen =f'{mins }m'
                else :
                    last_seen =t ('map.unknown.lastseen')if t else 'Unknown'
                base_ids =g_val ['RawData']['value'].get ('base_ids',[])
                valid_bases =[]
                for bid in base_ids :
                    bid_str =str (bid ).replace ('-','')
                    if bid_str in base_map :
                        base_val =base_map [bid_str ]
                        try :
                            translation =base_val ['RawData']['value']['transform']['translation']
                            bx ,by =palworld_coord .sav_to_map (translation ['x'],translation ['y'],new =True )
                            if bx is not None :
                                img_x ,img_y =self ._to_image_coordinates (bx ,by ,self .map_width ,self .map_height )
                                # Convert to Old coordinates for display
                                save_x ,save_y =palworld_coord .map_to_sav (bx ,by ,new =True )
                                old_bx ,old_by =palworld_coord .sav_to_map (save_x ,save_y ,new =False )
                                valid_bases .append ({
                                'base_id':bid ,
                                'coords':(old_bx ,old_by ),
                                'img_coords':(img_x ,img_y ),
                                'data':{'key':bid ,'value':base_val },
                                'guild_id':gid ,
                                'guild_name':g_val ['RawData']['value'].get ('guild_name',t ('map.unknown.guild')if t else 'Unknown'),
                                'leader_name':leader_name 
                                })
                        except :
                            pass
                guilds [gid ]={
                'guild_name':g_val ['RawData']['value'].get ('guild_name',t ('map.unknown.guild')if t else 'Unknown'),
                'leader_name':leader_name ,
                'last_seen':last_seen ,
                'bases':valid_bases 
                }
        except Exception as e :
            print (f"Error getting guild bases: {e }")
        return guilds 
    def _to_image_coordinates (self ,x_world ,y_world ,width ,height ):
        x_min ,x_max =-1000 ,1000 
        y_min ,y_max =-1000 ,1000 
        x_scale =width /(x_max -x_min )
        y_scale =height /(y_max -y_min )
        img_x =int ((x_world -x_min )*x_scale )
        img_y =int ((y_max -y_world )*y_scale )
        return img_x ,img_y 
    def _update_markers (self ):
        for marker in self .base_markers :
            self .scene .removeItem (marker )
        self .base_markers .clear ()
        if self .config ['marker']['type']=='dot':
            marker_pixmap =self ._create_dot_pixmap (int (self .config ['marker']['dot']['size']))
        else :
            marker_pixmap =self .base_icon_pixmap 
        for guild in self .filtered_guilds .values ():
            for base in guild ['bases']:
                img_x ,img_y =base ['img_coords']
                marker =BaseMarker (base ,img_x ,img_y ,marker_pixmap ,self .config )
                marker .scale_to_zoom (self .view .current_zoom )
                self .scene .addItem (marker )
                self .base_markers .append (marker )
    def _update_tree (self ):
        self .guild_tree .clear ()
        for gid ,guild in self .filtered_guilds .items ():
            guild_item =QTreeWidgetItem ([
            guild ['guild_name'],
            guild ['leader_name'],
            guild ['last_seen'],
            str (len (guild ['bases']))
            ])
            guild_item .setData (0 ,Qt .UserRole ,('guild',gid ))
            for base in guild ['bases']:
                base_item =QTreeWidgetItem ([
                f"X:{int (base ['coords'][0 ])} Y:{int (base ['coords'][1 ])}",
                str (base ['base_id'])[:12 ]+'...',
                '',
                ''
                ])
                base_item .setData (0 ,Qt .UserRole ,('base',base ))
                base_item .setForeground (0 ,QColor (0 ,180 ,255 ))
                guild_item .addChild (base_item )
            self .guild_tree .addTopLevelItem (guild_item )
    def _on_search_changed (self ,text ):
        self .search_text =text .lower ()
        if not text :
            self .filtered_guilds =self .guilds_data 
        else :
            terms =text .lower ().split ()
            filtered ={}
            for gid ,guild in self .guilds_data .items ():
                gn =guild ['guild_name'].lower ()
                ln =guild ['leader_name'].lower ()
                ls =guild ['last_seen'].lower ()
                guild_matches =all (any (term in field for field in [gn ,ln ,ls ])for term in terms )
                matching_bases =[
                b for b in guild ['bases']
                if all (any (term in field for field in [
                str (b ['base_id']).lower (),
                f"x:{int (b ['coords'][0 ])}, y:{int (b ['coords'][1 ])}",
                gn ,ln ,ls 
                ])for term in terms )
                ]
                if guild_matches or matching_bases :
                    filtered [gid ]=dict (guild )
                    if not guild_matches :
                        filtered [gid ]['bases']=matching_bases 
            self .filtered_guilds =filtered 
        self ._update_markers ()
        self ._update_tree ()
    def _on_item_expanded (self ,item ):
        pass 
    def _on_tree_item_clicked (self ,item ,column ):
        data =item .data (0 ,Qt .UserRole )
        if not data :
            return 
        item_type ,item_data =data 
        if item_type =='base':
            self ._update_info (item_data )
            self ._highlight_base (item_data )
            self ._zoom_to_base (item_data )
    def _on_tree_item_double_clicked (self ,item ,column ):
        data =item .data (0 ,Qt .UserRole )
        if not data :
            return 
        item_type ,item_data =data 
        if item_type =='base':
            self ._update_info (item_data )
            self ._zoom_to_base (item_data ,zoom_level =self .config ['zoom']['double_click_target'])
    def _highlight_base (self ,base_data ):
        for marker in self .base_markers :
            if marker .base_data ==base_data :
                self .scene .clearSelection ()
                marker .setSelected (True )
                marker .start_glow ()
                break 
    def _zoom_to_base (self ,base_data ,zoom_level =6.0 ):
        for marker in self .base_markers :
            if marker .base_data ['base_id']==base_data ['base_id']:
                self .scene .clearSelection ()
                marker .setSelected (True )
                marker .start_glow ()
                self .view .animate_to_marker (marker ,zoom_level =zoom_level )
                break 
    def _play_effect (self ,effect_class ,x ,y ):
        effect =effect_class (x ,y )
        self .scene .addItem (effect )
        self .active_effects .append (effect )
        anim =QPropertyAnimation (effect ,b"progress")
        anim .setDuration (effect .duration )
        anim .setStartValue (0.0 )
        anim .setEndValue (1.0 )
        anim .setEasingCurve (QEasingCurve .OutCubic )
        def cleanup ():
            self .scene .removeItem (effect )
            if effect in self .active_effects :
                self .active_effects .remove (effect )
        anim .finished .connect (cleanup )
        anim .start ()
        effect ._animation =anim 
    def _update_info (self ,base_data ):
        info =f"""
        <b>Guild:</b> {base_data ['guild_name']}<br>
        <b>Leader:</b> {base_data ['leader_name']}<br>
        <b>Base ID:</b> {str (base_data ['base_id'])[:16 ]}...<br>
        <b>Coordinates:</b> X:{int (base_data ['coords'][0 ])}, Y:{int (base_data ['coords'][1 ])}
        """
        self .info_label .setText (info .strip ())
    def _on_marker_clicked (self ,base_data ):
        self ._update_info (base_data )
        self ._zoom_to_base (base_data )
    def _on_marker_double_clicked (self ,base_data ):
        self ._update_info (base_data )
    def _on_zoom_changed (self ,zoom_level ):
        for marker in self .base_markers :
            marker .scale_to_zoom (zoom_level )
    def _on_marker_right_clicked (self ,base_data ,global_pos ):
        self ._zoom_to_base (base_data )
        menu =QMenu (self )
        menu .setStyleSheet ("""
            QMenu {
                background-color: rgba(18, 20, 24, 0.95);
                border: 1px solid rgba(125, 211, 252, 0.3);
                border-radius: 4px;
                color: #e2e8f0;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 12px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: rgba(59, 142, 208, 0.3);
            }
        """)
        delete_action =menu .addAction (t ('delete.base')if t else 'Delete Base')
        export_action =menu .addAction (t ('button.export')if t else 'Export Base')
        action =menu .exec (global_pos .toPoint ())
        if action ==delete_action :
            self ._delete_base (base_data )
        elif action ==export_action :
            self ._export_base (base_data )
    def _on_tree_context_menu (self ,pos ):
        item =self .guild_tree .itemAt (pos )
        if not item :
            return 
        data =item .data (0 ,Qt .UserRole )
        if not data :
            return 
        item_type ,item_data =data 
        menu =QMenu (self )
        menu .setStyleSheet ("""
            QMenu {
                background-color: rgba(18, 20, 24, 0.95);
                border: 1px solid rgba(125, 211, 252, 0.3);
                border-radius: 4px;
                color: #e2e8f0;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 12px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: rgba(59, 142, 208, 0.3);
            }
        """)
        if item_type =='base':
            self ._zoom_to_base (item_data )
            delete_action =menu .addAction (t ('delete.base')if t else 'Delete Base')
            export_action =menu .addAction (t ('button.export')if t else 'Export Base')
            action =menu .exec (self .guild_tree .viewport ().mapToGlobal (pos ))
            if action ==delete_action :
                self ._delete_base (item_data )
            elif action ==export_action :
                self ._export_base (item_data )
        elif item_type =='guild':
            rename_action =menu .addAction (t ('guild.rename.title')if t else 'Rename Guild')
            delete_action =menu .addAction (t ('delete.guild')if t else 'Delete Guild')
            import_action =menu .addAction (t ('button.import')if t else 'Import Base')
            action =menu .exec (self .guild_tree .viewport ().mapToGlobal (pos ))
            if action ==rename_action :
                self ._rename_guild (item_data )
            elif action ==delete_action :
                self ._delete_guild (item_data )
            elif action ==import_action :
                self ._import_base_to_guild (item_data )
    def _delete_base (self ,base_data ):
        if str (base_data ['base_id'])in constants .exclusions .get ('bases',[]):
            QMessageBox .warning (self ,t ('warning.title')if t else 'Warning',t ('deletion.warning.protected_base')if t else f'Base {base_data ["base_id"]} is in exclusion list and cannot be deleted.')
            return 
        reply =QMessageBox .question (
        self ,
        t ('confirm.title')if t else 'Confirm',
        t ('confirm.delete_base')if t else f'Delete base at X:{int (base_data ["coords"][0 ])}, Y:{int (base_data ["coords"][1 ])}?',
        QMessageBox .Yes |QMessageBox .No 
        )
        if reply ==QMessageBox .Yes :
            try :
                img_x ,img_y =base_data ['img_coords']
                self ._play_effect (DeleteEffect ,img_x ,img_y )
                base_entry =base_data ['data']
                guild_id =base_data ['guild_id']
                delete_base_camp (base_entry ,guild_id )
                self .refresh ()
                if self .parent_window :
                    self .parent_window .refresh_all ()
                QMessageBox .information (
                self ,
                t ('success.title')if t else 'Success',
                t ('base.delete.success')if t else 'Base deleted successfully'
                )
            except Exception as e :
                QMessageBox .critical (
                self ,
                t ('error.title')if t else 'Error',
                f'Failed to delete base: {str (e )}'
                )
    def _export_base (self ,base_data ):
        try :
            bid =str (base_data ['base_id'])
            data =export_base_json (constants .loaded_level_json ,bid )
            if not data :
                QMessageBox .warning (
                self ,
                t ('error.title')if t else 'Error',
                t ('base.export.not_found')if t else 'Base data not found'
                )
                return 
            default_name =f'base_{bid [:8 ]}.json'
            file_path ,_ =QFileDialog .getSaveFileName (
            self ,
            t ('base.export.title')if t else 'Export Base',
            default_name ,
            'JSON Files (*.json)'
            )
            if file_path :
                class CustomEncoder (json .JSONEncoder ):
                    def default (self ,obj ):
                        if hasattr (obj ,'bytes')or obj .__class__ .__name__ =='UUID':
                            return str (obj )
                        return super ().default (obj )
                with open (file_path ,'w',encoding ='utf-8')as f :
                    json .dump (data ,f ,cls =CustomEncoder ,indent =2 )
                img_x ,img_y =base_data ['img_coords']
                self ._play_effect (ExportEffect ,img_x ,img_y )
                QMessageBox .information (
                self ,
                t ('success.title')if t else 'Success',
                t ('base.export.success')if t else 'Base exported successfully'
                )
        except Exception as e :
            QMessageBox .critical (
            self ,
            t ('error.title')if t else 'Error',
            f'Failed to export base: {str (e )}'
            )
    def _rename_guild (self ,guild_id ):
        current_name =self .guilds_data .get (guild_id ,{}).get ('guild_name','')
        new_name ,ok =QInputDialog .getText (
        self ,
        t ('guild.rename.title')if t else 'Rename Guild',
        t ('guild.rename.prompt')if t else 'Enter new guild name:',
        text =current_name 
        )
        if ok and new_name :
            try :
                rename_guild (guild_id ,new_name )
                self .refresh ()
                if self .parent_window :
                    self .parent_window .refresh_all ()
                QMessageBox .information (
                self ,
                t ('success.title')if t else 'Success',
                t ('guild.rename.success')if t else 'Guild renamed successfully'
                )
            except Exception as e :
                QMessageBox .critical (
                self ,
                t ('error.title')if t else 'Error',
                f'Failed to rename guild: {str (e )}'
                )
    def _delete_guild (self ,guild_id ):
        from ..data_manager import delete_guild ,load_exclusions 
        guild_name =self .guilds_data .get (guild_id ,{}).get ('guild_name','Unknown')
        base_count =len (self .guilds_data .get (guild_id ,{}).get ('bases',[]))
        load_exclusions ()
        guild_id_clean =str (guild_id ).replace ('-','').lower ()
        if guild_id_clean in [ex .replace ('-','').lower ()for ex in constants .exclusions .get ('guilds',[])]:
            QMessageBox .warning (self ,t ('warning.title')if t else 'Warning',t ('deletion.warning.protected_guild')if t else f'Guild {guild_id } is in exclusion list and cannot be deleted.')
            return 
        wsd =constants .loaded_level_json ['properties']['worldSaveData']['value']
        for b in wsd .get ('BaseCampSaveData',{}).get ('value',[]):
            try :
                from ..utils import are_equal_uuids 
                base_gid =str (b ['value']['RawData']['value'].get ('group_id_belong_to','')).replace ('-','').lower ()
                base_id =str (b ['key']).replace ('-','').lower ()
                if base_gid ==guild_id_clean :
                    if base_id in [ex .replace ('-','').lower ()for ex in constants .exclusions .get ('bases',[])]:
                        QMessageBox .warning (
                        self ,
                        t ('warning.title')if t else 'Warning',
                        f'Guild "{guild_name }" has bases in exclusion list and cannot be deleted.\nExcluded base: {base_id }'
                        )
                        return 
            except :
                pass 
        for g in wsd .get ('GroupSaveDataMap',{}).get ('value',[]):
            try :
                g_id =str (g ['key']).replace ('-','').lower ()
                if g_id ==guild_id_clean :
                    if g ['value']['GroupType']['value']['value']=='EPalGroupType::Guild':
                        for p in g ['value']['RawData']['value'].get ('players',[]):
                            player_id =str (p .get ('player_uid','')).replace ('-','').lower ()
                            if player_id in [ex .replace ('-','').lower ()for ex in constants .exclusions .get ('players',[])]:
                                QMessageBox .warning (
                                self ,
                                t ('warning.title')if t else 'Warning',
                                f'Guild "{guild_name }" has players in exclusion list and cannot be deleted.\nExcluded player: {player_id }'
                                )
                                return 
                    break 
            except :
                pass 
        reply =QMessageBox .question (
        self ,
        t ('confirm.title')if t else 'Confirm',
        f'Delete guild "{guild_name }" and all {base_count } bases?\n\nThis will also delete all characters owned by guild members.',
        QMessageBox .Yes |QMessageBox .No 
        )
        if reply ==QMessageBox .Yes :
            try :
                if delete_guild (guild_id ):
                    self .refresh ()
                    if self .parent_window :
                        self .parent_window .refresh_all ()
                    QMessageBox .information (
                    self ,
                    t ('success.title')if t else 'Success',
                    t ('guild.delete.success')if t else 'Guild and all bases deleted successfully'
                    )
                else :
                    QMessageBox .warning (
                    self ,
                    t ('error.title')if t else 'Error',
                    'Failed to delete guild - guild not found or not a guild type'
                    )
            except Exception as e :
                QMessageBox .critical (
                self ,
                t ('error.title')if t else 'Error',
                f'Failed to delete guild: {str (e )}'
                )
    def _import_base_to_guild (self ,guild_id ):
        file_path ,_ =QFileDialog .getOpenFileName (
        self ,
        t ('button.import')if t else 'Import Base',
        '',
        'JSON Files (*.json)'
        )
        if not file_path :
            return 
        try :
            with open (file_path ,'r',encoding ='utf-8')as f :
                exported_data =json .load (f )
            if import_base_json (constants .loaded_level_json ,exported_data ,guild_id ):
                imported_coords =None 
                try :
                    raw_t =exported_data ['base_camp']['value']['RawData']['value']['transform']['translation']
                    bx ,by =palworld_coord .sav_to_map (raw_t ['x'],raw_t ['y'],new =True )
                    img_x ,img_y =self ._to_image_coordinates (bx ,by ,self .map_width ,self .map_height )
                    imported_coords =(bx ,by ,img_x ,img_y )
                    self ._play_effect (ImportEffect ,img_x ,img_y )
                except :
                    pass 
                self .refresh ()
                if self .parent_window :
                    self .parent_window .refresh_all ()
                if imported_coords :
                    world_x ,world_y ,img_x ,img_y =imported_coords 
                    for marker in self .base_markers :
                        base_coords =marker .base_data ['coords']
                        if abs (base_coords [0 ]-world_x )<1 and abs (base_coords [1 ]-world_y )<1 :
                            zoom_level =self .config ['zoom']['double_click_target']
                            self .view .animate_to_marker (marker ,zoom_level =zoom_level )
                            self .scene .clearSelection ()
                            marker .setSelected (True )
                            marker .start_glow ()
                            break 
                QMessageBox .information (
                self ,
                t ('success.title')if t else 'Success',
                t ('base.import.success')if t else 'Base imported successfully'
                )
            else :
                QMessageBox .warning (
                self ,
                t ('error.title')if t else 'Error',
                'Import failed'
                )
        except Exception as e :
            QMessageBox .critical (
            self ,
            t ('error.title')if t else 'Error',
            f'Failed to import base: {str (e )}'
            )
