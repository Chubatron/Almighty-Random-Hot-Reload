"""
Dice Screen - экран с кубиками из спрайт-листа
"""
import os
import random
import math
from kivy.app import App
from kivy.uix.image import Image
from kivy.properties import StringProperty, NumericProperty
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.utils import platform
from kivy.core.audio import SoundLoader

from screens.base_game_screen import BaseGameScreen
from screens.dice import (
    DropZone, PointMarker, DiceWidget, GlassWidget, ShadowWidget
)

# ===== НАСТРОЙКИ ОТЛАДКИ =====
DEBUG_MODE = False
# =============================


class DiceScreen(BaseGameScreen):
    """Экран с кубиками на столе и стаканом рядом"""

    background_image = StringProperty('assets/backgrounds/dice_bg.png')
    sprite_sheet_path = StringProperty('assets/sprites/dice_spritesheet.png')
    glass_sprite_sheet_path = StringProperty('assets/sprites/spritesheet_glass12.png')
    shadow_sprite_sheet_path = StringProperty('assets/sprites/spritesheet_shadow.png')

    shadow_scale_factor = NumericProperty(2.6)
    shadow_rotation = NumericProperty(-90)
    shadow_offset_x_factor = NumericProperty(-1.25)
    shadow_offset_y_factor = NumericProperty(-0.35)
    shadow_opacity = NumericProperty(0.7)
    shadow_move_factor_x = NumericProperty(-1.0)
    shadow_move_factor_y = NumericProperty(0.0)

    ANIMATION_DURATION = 1.5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.disappear_duration = 0.5
        self.appear_duration = 0.6
        self.overlap_time = 0.2

        self.dice_size = 0
        self.large_dice_size = 0
        self.glass_size = 0
        self.shadow_size = 0

        self.START_POSITION_DICE_X = 0
        self.START_POSITION_DICE_Y = 0
        self.START_POSITION_GLASS_X = 0
        self.START_POSITION_GLASS_Y = 0
        self.SHADOW_POSITION_X = 0
        self.SHADOW_POSITION_Y = 0
        self.SHADOW_TARGET_POSITION_X = 0
        self.SHADOW_TARGET_POSITION_Y = 0

        self.dice_list = []
        self.glass = None
        self.shadow = None
        self.drop_zone = None
        self.point_a_marker = None
        self.current_mode = 1
        self.bg = None
        self.is_animating = False
        self.animation_counter = 0
        self.dice_hidden = False
        self.pending_hide_dice = False

        self.glass_start_pos = None
        self.glass_target_pos = None
        self.is_at_target = True

        self.last_dice_center = None

        self.last_touch_pos = None
        self.last_touch_time = None
        self.max_speed = 0

        self.sound_glass_lower = None
        self.sound_glass_raise = None
        self.sound_dice_roll = None
        self.sound_glass_drag = None
        self.sound_dice_appear = None
        self.sound_dice_disappear = None

        self.volume_fade_clock = None
        self.target_volume = 0.0

        self.is_dice_enlarged = False
        self.is_glass_blocked = False
        self.is_dice_blocked = False

    def get_screen_size(self):
        if platform == 'android':
            width, height = Window.system_size
        else:
            width = Window.width
            height = Window.height
        return width, height

    def _get_center_positions(self):
        screen_width, screen_height = self.get_screen_size()
        center_x = screen_width / 2
        pos1_y = screen_height * 0.33
        pos2_y = screen_height * 0.5
        pos3_y = screen_height * 0.66
        return {
            'pos1': (center_x, pos1_y),
            'pos2': (center_x, pos2_y),
            'pos3': (center_x, pos3_y)
        }

    def _get_dice_target_position(self, dice, mode='grow'):
        positions = self._get_center_positions()
        if mode == 'grow':
            if len(self.dice_list) == 1:
                target_x = positions['pos2'][0] - dice.width / 2
                target_y = positions['pos2'][1] - dice.height / 2
                return (target_x, target_y)
            else:
                index = self.dice_list.index(dice) if dice in self.dice_list else 0
                if index == 0:
                    target_x = positions['pos1'][0] - dice.width / 2
                    target_y = positions['pos1'][1] - dice.height / 2
                else:
                    target_x = positions['pos3'][0] - dice.width / 2
                    target_y = positions['pos3'][1] - dice.height / 2
                return (target_x, target_y)
        else:
            if hasattr(dice, 'original_position') and dice.original_position:
                return dice.original_position
            return (self.START_POSITION_DICE_X, dice.pos[1] if len(self.dice_list) > 1 else self.START_POSITION_DICE_Y)

    def _get_dice_original_positions(self):
        screen_width, screen_height = self.get_screen_size()
        positions = {}
        if len(self.dice_list) == 1:
            x = self.START_POSITION_DICE_X
            y = self.START_POSITION_DICE_Y
            positions[0] = (x, y)
        else:
            distance_between = self.dice_size * 0.3
            center_y = self.START_POSITION_DICE_Y + (self.large_dice_size // 2) - (self.dice_size // 2)
            y_top = center_y - distance_between
            y_bottom = center_y + distance_between
            positions[0] = (self.START_POSITION_DICE_X, y_top)
            positions[1] = (self.START_POSITION_DICE_X, y_bottom)
        return positions

    def _load_dice_sounds(self):
        try:
            if os.path.exists('assets/sounds/dice/glass_lower.mp3'):
                self.sound_glass_lower = SoundLoader.load('assets/sounds/dice/glass_lower.mp3')
                if self.sound_glass_lower:
                    print("✅ Загружен звук: glass_lower.mp3")

            if os.path.exists('assets/sounds/dice/glass_raise.mp3'):
                self.sound_glass_raise = SoundLoader.load('assets/sounds/dice/glass_raise.mp3')
                if self.sound_glass_raise:
                    print("✅ Загружен звук: glass_raise.mp3")

            if os.path.exists('assets/sounds/dice/dice_roll.mp3'):
                self.sound_dice_roll = SoundLoader.load('assets/sounds/dice/dice_roll.mp3')
                if self.sound_dice_roll:
                    print("✅ Загружен звук: dice_roll.mp3")

            if os.path.exists('assets/sounds/dice/glass_drag.mp3'):
                self.sound_glass_drag = SoundLoader.load('assets/sounds/dice/glass_drag.mp3')
                if self.sound_glass_drag:
                    self.sound_glass_drag.loop = True
                    self.sound_glass_drag.volume = 0.0
                    self.sound_glass_drag.play()
                    print("✅ Загружен звук: glass_drag.mp3 (зацикленный)")

            if os.path.exists('assets/sounds/dice/dice_appear.mp3'):
                self.sound_dice_appear = SoundLoader.load('assets/sounds/dice/dice_appear.mp3')
                if self.sound_dice_appear:
                    print("✅ Загружен звук: dice_appear.mp3")

            if os.path.exists('assets/sounds/dice/dice_disappear.mp3'):
                self.sound_dice_disappear = SoundLoader.load('assets/sounds/dice/dice_disappear.mp3')
                if self.sound_dice_disappear:
                    print("✅ Загружен звук: dice_disappear.mp3")

        except Exception as e:
            print(f"Ошибка загрузки звуков кубиков: {e}")

    def _fade_volume(self, target_volume, duration=0.2):
        if not self.sound_glass_drag:
            return

        self.target_volume = target_volume
        start_volume = self.sound_glass_drag.volume

        if self.volume_fade_clock:
            self.volume_fade_clock.cancel()
            self.volume_fade_clock = None

        def update_volume(step, steps):
            if step <= 0:
                self.sound_glass_drag.volume = target_volume
                self.volume_fade_clock = None
                return

            progress = step / steps
            self.sound_glass_drag.volume = start_volume + (target_volume - start_volume) * (1 - progress)

            self.volume_fade_clock = Clock.schedule_once(
                lambda dt: update_volume(step - 1, steps),
                duration / steps
            )

        steps = 20
        update_volume(steps, steps)

    def play_dice_roll_sound(self):
        if self.sound_dice_roll and not self.sound_manager.is_muted():
            self.sound_dice_roll.play()

    def play_dice_appear_sound(self):
        if self.sound_dice_appear and not self.sound_manager.is_muted():
            self.sound_dice_appear.play()

    def play_dice_disappear_sound(self):
        if self.sound_dice_disappear and not self.sound_manager.is_muted():
            self.sound_dice_disappear.play()

    def _block_glass(self):
        self.is_glass_blocked = True
        if DEBUG_MODE:
            print("🔒 [GLASS] Стакан заблокирован")

    def _unblock_glass(self):
        self.is_glass_blocked = False
        if DEBUG_MODE:
            print("🔓 [GLASS] Стакан разблокирован")

    def _block_dice(self):
        self.is_dice_blocked = True
        if DEBUG_MODE:
            print("🔒 [DICE] Кубики заблокированы")

    def _unblock_dice(self):
        self.is_dice_blocked = False
        if DEBUG_MODE:
            print("🔓 [DICE] Кубики разблокированы")

    def _animate_dice_grow_with_move(self, dice, target_size, target_position, on_complete_callback=None):
        if hasattr(dice, 'is_animating_scale') and dice.is_animating_scale:
            return
        dice.is_animating_scale = True

        self._block_glass()

        if dice.original_center is None:
            original_center_x = dice.pos[0] + dice.width / 2
            original_center_y = dice.pos[1] + dice.height / 2
            dice.original_center = (original_center_x, original_center_y)

        positions = self._get_center_positions()

        if len(self.dice_list) == 1:
            target_center_x = positions['pos2'][0]
            target_center_y = positions['pos2'][1]
        else:
            index = self.dice_list.index(dice) if dice in self.dice_list else 0
            if index == 0:
                target_center_x = positions['pos1'][0]
                target_center_y = positions['pos1'][1]
            else:
                target_center_x = positions['pos3'][0]
                target_center_y = positions['pos3'][1]

        corrected_target_x = target_center_x - target_size / 2
        corrected_target_y = target_center_y - target_size / 2
        target_position = (corrected_target_x, corrected_target_y)

        if dice.glow:
            anim_glow_fade = Animation(opacity=0, duration=0.3)
            anim_glow_fade.start(dice.glow)

        current_frame = dice.frame_index
        dice.animate_rotation(current_frame, num_rotations=5, duration=self.ANIMATION_DURATION)

        anim_grow = Animation(dice_size=target_size, duration=self.ANIMATION_DURATION, t='linear')
        anim_move = Animation(pos=target_position, duration=self.ANIMATION_DURATION, t='linear')

        def on_complete(*args):
            dice.is_animating_scale = False
            self.is_dice_enlarged = True
            dice.enlarged_size = target_size
            self._unblock_dice()
            if on_complete_callback:
                on_complete_callback()

        anim_grow.bind(on_complete=on_complete)
        anim_grow.start(dice)
        anim_move.start(dice)

    def _animate_dice_shrink_with_move(self, dice, original_size, on_complete_callback=None):
        if hasattr(dice, 'is_animating_scale') and dice.is_animating_scale:
            return
        dice.is_animating_scale = True

        if dice.original_center is None:
            original_center_x = dice.pos[0] + dice.width / 2
            original_center_y = dice.pos[1] + dice.height / 2
        else:
            original_center_x, original_center_y = dice.original_center

        corrected_original_x = original_center_x - original_size / 2
        corrected_original_y = original_center_y - original_size / 2
        target_position = (corrected_original_x, corrected_original_y)

        current_frame = dice.frame_index
        dice.animate_rotation(current_frame, num_rotations=5, duration=self.ANIMATION_DURATION)

        if dice.glow:
            dice.glow.opacity = 0
            Clock.schedule_once(lambda dt: self._appear_glow(dice.glow), self.ANIMATION_DURATION - 0.3)

        anim_shrink = Animation(dice_size=original_size, duration=self.ANIMATION_DURATION, t='linear')
        anim_move_back = Animation(pos=target_position, duration=self.ANIMATION_DURATION, t='linear')

        def on_complete(*args):
            dice.is_animating_scale = False
            dice.original_center = None
            if on_complete_callback:
                on_complete_callback()

        anim_shrink.bind(on_complete=on_complete)
        anim_shrink.start(dice)
        anim_move_back.start(dice)

    def _appear_glow(self, glow):
        if glow:
            anim = Animation(opacity=1, duration=0.1)
            anim.start(glow)

    def _animate_dice_appearance(self):
        self._block_dice()

        original_positions = self._get_dice_original_positions()

        completed_animations = [0]
        total_dice = len(self.dice_list)

        def check_all_complete():
            completed_animations[0] += 1
            if completed_animations[0] >= total_dice:
                pass

        for i, dice in enumerate(self.dice_list):
            if not hasattr(dice, 'original_position') or dice.original_position is None:
                dice.original_position = original_positions.get(i, dice.pos)

            if not hasattr(dice, 'original_size') or dice.original_size is None:
                dice.original_size = dice.dice_size

            if dice.original_center is None:
                original_center_x = dice.pos[0] + dice.width / 2
                original_center_y = dice.pos[1] + dice.height / 2
                dice.original_center = (original_center_x, original_center_y)

            target_size = dice.original_size * 5
            target_position = self._get_dice_target_position(dice, 'grow')

            self._animate_dice_grow_with_move(dice, target_size, target_position, check_all_complete)

    def _shrink_all_dice(self, on_complete_callback=None):
        if not self.is_dice_enlarged:
            if on_complete_callback:
                on_complete_callback()
            return

        self._block_dice()

        completed_animations = [0]
        total_dice = len(self.dice_list)

        def check_all_complete():
            completed_animations[0] += 1
            if completed_animations[0] >= total_dice:
                self.is_dice_enlarged = False
                self._unblock_glass()
                self._unblock_dice()
                if on_complete_callback:
                    on_complete_callback()

        for dice in self.dice_list:
            original_size = getattr(dice, 'original_size', dice.dice_size)
            self._animate_dice_shrink_with_move(dice, original_size, check_all_complete)

    def _raise_glass(self, on_complete_callback=None):
        self._block_dice()

        if self.sound_glass_raise and not self.sound_manager.is_muted():
            self.sound_glass_raise.play()

        shadow_target_pos = (self.SHADOW_TARGET_POSITION_X, self.SHADOW_TARGET_POSITION_Y)

        for dice in self.dice_list:
            if dice.glow:
                dice.glow.update_position(dice.pos, dice.dice_size)
            dice.enable_glow()

        def on_animation_complete(*args):
            self.is_at_target = False
            if self._on_glass_move_complete:
                self._on_glass_move_complete()
            if on_complete_callback:
                on_complete_callback()
            self._update_point_a_marker()
            self._unblock_dice()

        self.glass.animate_movement(
            start_pos=self.glass_start_pos,
            end_pos=self.glass_target_pos,
            duration=0.6,
            forward=True,
            callback=on_animation_complete
        )

        self.shadow.animate_movement_to_target(
            target_pos=shadow_target_pos,
            duration=0.6,
            forward=True
        )

    def _lower_glass(self):
        self._block_dice()

        self.max_speed = 0
        self.last_touch_pos = None
        self.last_touch_time = None

        self.shadow.pos = (self.SHADOW_TARGET_POSITION_X, self.SHADOW_TARGET_POSITION_Y)
        shadow_target_pos = (self.SHADOW_POSITION_X, self.SHADOW_POSITION_Y)

        def on_animation_complete(*args):
            self.is_at_target = True
            if self.sound_glass_lower and not self.sound_manager.is_muted():
                self.sound_glass_lower.play()
            if self._on_glass_move_complete:
                self._on_glass_move_complete()
            self._update_point_a_marker()
            self._unblock_dice()

        self.glass.animate_movement(
            start_pos=self.glass_target_pos,
            end_pos=self.glass_start_pos,
            duration=0.6,
            forward=False,
            callback=on_animation_complete
        )

        self.shadow.animate_movement_to_target(
            target_pos=shadow_target_pos,
            duration=0.6,
            forward=False
        )

    def _lower_glass_to_center(self, target_center_x, target_center_y):
        self._block_dice()

        self.max_speed = 0
        self.last_touch_pos = None
        self.last_touch_time = None

        old_start_x = self.glass_start_pos[0]
        old_start_y = self.glass_start_pos[1]
        old_target_x = self.glass_target_pos[0]
        old_target_y = self.glass_target_pos[1]
        old_shadow_x = self.SHADOW_POSITION_X
        old_shadow_y = self.SHADOW_POSITION_Y
        old_shadow_target_x = self.SHADOW_TARGET_POSITION_X
        old_shadow_target_y = self.SHADOW_TARGET_POSITION_Y

        new_start_x = target_center_x - self.glass_size / 6.5
        new_start_y = target_center_y - self.glass_size / 2

        offset_x = new_start_x - old_start_x
        offset_y = new_start_y - old_start_y

        self.shadow.pos = (old_shadow_target_x, old_shadow_target_y)
        shadow_target_pos = (old_shadow_x + offset_x, old_shadow_y + offset_y)

        Clock.schedule_once(lambda dt: self._disable_glow_for_all_dice(), 0.5)

        def on_animation_complete(*args):
            self.glass_start_pos = (new_start_x, new_start_y)
            self.glass_target_pos = (old_target_x + offset_x, old_target_y + offset_y)
            self.SHADOW_POSITION_X = old_shadow_x + offset_x
            self.SHADOW_POSITION_Y = old_shadow_y + offset_y
            self.SHADOW_TARGET_POSITION_X = old_shadow_target_x + offset_x
            self.SHADOW_TARGET_POSITION_Y = old_shadow_target_y + offset_y

            self.glass.pos = self.glass_start_pos
            self.shadow.move_by_delta(offset_x, offset_y)

            self.is_at_target = True

            if self.sound_glass_lower and not self.sound_manager.is_muted():
                self.sound_glass_lower.play()

            if self.pending_hide_dice:
                for dice in self.dice_list:
                    dice.opacity = 0
                    if dice.glow:
                        dice.glow.opacity = 0
                self.dice_hidden = True
                self.pending_hide_dice = False

            self._update_point_a_marker()
            self._unblock_dice()

            if self._on_glass_move_complete:
                self._on_glass_move_complete()

        self.glass.animate_movement(
            start_pos=self.glass_target_pos,
            end_pos=(new_start_x, new_start_y),
            duration=0.6,
            forward=False,
            callback=on_animation_complete
        )

        self.shadow.animate_movement_to_target(
            target_pos=shadow_target_pos,
            duration=0.6,
            forward=False
        )

    def _on_dice_click(self):
        if self.is_dice_blocked:
            if DEBUG_MODE:
                print("🔒 [DiceScreen] Кубики заблокированы, клик игнорируется")
            return

        if self.is_animating:
            return

        if self.is_dice_enlarged:
            self._shrink_all_dice()
        else:
            self._start_switch_animation()

    def on_enter(self):
        super().on_enter()
        self._load_dice_sounds()

        screen_width, screen_height = self.get_screen_size()

        self.dice_size = screen_width * 0.1
        self.large_dice_size = self.dice_size * 1.26
        self.glass_size = screen_width * 0.20
        self.shadow_size = self.glass_size * 0.9

        self.START_POSITION_DICE_X = screen_width * 0.3
        self.START_POSITION_DICE_Y = screen_height * 0.5 - (self.large_dice_size // 2)

        self.START_POSITION_GLASS_X = screen_width * 0.27
        self.START_POSITION_GLASS_Y = screen_height * 0.35

        self.SHADOW_POSITION_X = self.START_POSITION_GLASS_X + (self.glass_size * self.shadow_offset_x_factor)
        self.SHADOW_POSITION_Y = self.START_POSITION_GLASS_Y + (self.glass_size * self.shadow_offset_y_factor)

        self.glass_start_pos = (self.START_POSITION_GLASS_X, self.START_POSITION_GLASS_Y)
        self.glass_target_pos = (self.START_POSITION_GLASS_X + self.glass_size, self.START_POSITION_GLASS_Y - self.glass_size)

        self.SHADOW_TARGET_POSITION_X = self.SHADOW_POSITION_X + (self.glass_size * self.shadow_move_factor_x)
        self.SHADOW_TARGET_POSITION_Y = self.SHADOW_POSITION_Y - (self.glass_size * self.shadow_move_factor_y)

        self._setup_ui()

        Clock.schedule_once(lambda dt: self._create_drop_zone(), 0.1)

    def _create_drop_zone(self):
        screen_width, screen_height = self.get_screen_size()
        self.drop_zone = DropZone(screen_width, screen_height)
        self.layout.add_widget(self.drop_zone)

    def _create_point_a_marker(self):
        if DEBUG_MODE:
            self.point_a_marker = PointMarker(color=(1, 0, 0, 1), size=10)
        else:
            self.point_a_marker = PointMarker(color=(1, 1, 1, 0.4), size=2)

        self.layout.add_widget(self.point_a_marker, index=0)
        self._update_point_a_marker()

    def _update_point_a_marker(self):
        if self.point_a_marker and self.drop_zone:
            point_a_x = self.glass_start_pos[0] + self.glass_size / 6.5
            point_a_y = self.glass_start_pos[1] + self.glass_size / 2

            if DEBUG_MODE:
                in_zone = self.drop_zone.check_point_in_zone(point_a_x, point_a_y)
                if in_zone:
                    self.point_a_marker.color = (0, 1, 0, 1)
                else:
                    self.point_a_marker.color = (1, 0, 0, 1)
            else:
                self.point_a_marker.color = (1, 1, 1, 0.4)

            self.point_a_marker.update_position(point_a_x, point_a_y, visible=True)
            return in_zone if DEBUG_MODE else True
        return True

    def on_leave(self):
        if self.volume_fade_clock:
            self.volume_fade_clock.cancel()
            self.volume_fade_clock = None
        if self.sound_glass_drag:
            try:
                self.sound_glass_drag.stop()
            except:
                pass
        self._clear_all_dice()
        if self.glass and self.glass.parent:
            self.layout.remove_widget(self.glass)
            self.glass = None
        if self.shadow and self.shadow.parent:
            self.layout.remove_widget(self.shadow)
            self.shadow = None
        if self.drop_zone and self.drop_zone.parent:
            self.layout.remove_widget(self.drop_zone)
            self.drop_zone = None
        if self.point_a_marker and self.point_a_marker.parent:
            self.layout.remove_widget(self.point_a_marker)
            self.point_a_marker = None
        if self.bg and self.bg.parent:
            self.layout.remove_widget(self.bg)
            self.bg = None
        super().on_leave()

    def _setup_ui(self):
        if os.path.exists(self.background_image):
            self.bg = Image(source=self.background_image, allow_stretch=True, keep_ratio=False, size_hint=(1, 1))
            self.layout.add_widget(self.bg, index=0)

        self._create_point_a_marker()
        self._create_shadow()
        self._create_dice_for_mode(1, animate=False)
        self._create_glass()

    def _create_shadow(self):
        offset_x_px = self.glass_size * self.shadow_offset_x_factor
        offset_y_px = self.glass_size * self.shadow_offset_y_factor

        self.shadow = ShadowWidget(
            sprite_sheet_path=self.shadow_sprite_sheet_path,
            shadow_size=self.shadow_size,
            rows=2,
            cols=12,
            frame_index=0,
            rotation_angle=self.shadow_rotation,
            scale_factor=self.shadow_scale_factor,
            offset_x=offset_x_px,
            offset_y=offset_y_px,
            opacity=self.shadow_opacity,
            move_factor_x=self.shadow_move_factor_x,
            move_factor_y=self.shadow_move_factor_y,
            glass_size=self.glass_size,
            size_hint=(None, None),
            size=(self.shadow_size * self.shadow_scale_factor, self.shadow_size * self.shadow_scale_factor),
            pos=(self.SHADOW_POSITION_X, self.SHADOW_POSITION_Y)
        )
        self.shadow.set_frame(0)
        self.layout.add_widget(self.shadow)

    def _create_glass(self):
        self.glass = GlassWidget(
            sprite_sheet_path=self.glass_sprite_sheet_path,
            glass_size=self.glass_size,
            rows=2,
            cols=12,
            frame_index=0,
            rotation_angle=-90,
            size_hint=(None, None),
            size=(self.glass_size, self.glass_size),
            pos=self.glass_start_pos,
            on_glass_click=self._on_glass_click,
            on_glass_drag=self._on_glass_drag,
            on_glass_drag_end=self._on_glass_drag_end
        )
        self.glass.set_frame(0)
        self.layout.add_widget(self.glass)
        self.is_at_target = True

    def _update_dice_position(self, delta_x, delta_y):
        if not self.dice_list:
            return
        for dice in self.dice_list:
            new_x = dice.pos[0] + delta_x
            new_y = dice.pos[1] + delta_y
            dice.pos = (new_x, new_y)
            if dice.glow:
                dice.glow.update_position(dice.pos, dice.dice_size)

    def _on_glass_drag(self, delta_x, delta_y, touch):
        if self.is_glass_blocked:
            if DEBUG_MODE:
                print("🔒 [GLASS] Стакан заблокирован, перетаскивание игнорируется")
            return

        if self.is_animating:
            return
        if delta_x == 0 and delta_y == 0:
            return

        if self.is_at_target:
            current_time = Clock.get_time()
            current_pos = (touch.x, touch.y)

            if self.last_touch_pos is None or self.last_touch_time is None:
                self.last_touch_pos = current_pos
                self.last_touch_time = current_time
                current_speed = 0
            else:
                dx = current_pos[0] - self.last_touch_pos[0]
                dy = current_pos[1] - self.last_touch_pos[1]
                distance = math.sqrt(dx * dx + dy * dy)
                dt = current_time - self.last_touch_time
                if dt > 0:
                    current_speed = distance / dt
                    if current_speed > self.max_speed:
                        self.max_speed = current_speed
                else:
                    current_speed = 0
                self.last_touch_pos = current_pos
                self.last_touch_time = current_time

            MIN_SPEED = 50
            MAX_SPEED = 800
            MIN_VOLUME = 0.0
            MAX_VOLUME = 0.5

            if current_speed > MIN_SPEED:
                target_volume = MIN_VOLUME + (current_speed - MIN_SPEED) / (MAX_SPEED - MIN_SPEED) * (MAX_VOLUME - MIN_VOLUME)
                target_volume = max(MIN_VOLUME, min(MAX_VOLUME, target_volume))
            else:
                target_volume = 0.0

            if self.sound_glass_drag and not self.sound_manager.is_muted():
                if abs(target_volume - self.sound_glass_drag.volume) > 0.1:
                    self._fade_volume(target_volume, 0.1)
                else:
                    self.sound_glass_drag.volume = target_volume
        else:
            if self.sound_glass_drag:
                self._fade_volume(0.0, 0.2)

        if self.dice_hidden:
            self._update_dice_position(delta_x, delta_y)

        new_glass_x = self.glass.pos[0] + delta_x
        new_glass_y = self.glass.pos[1] + delta_y

        self.glass_start_pos = (self.glass_start_pos[0] + delta_x, self.glass_start_pos[1] + delta_y)
        self.glass_target_pos = (self.glass_target_pos[0] + delta_x, self.glass_target_pos[1] + delta_y)
        self.SHADOW_POSITION_X += delta_x
        self.SHADOW_POSITION_Y += delta_y
        self.SHADOW_TARGET_POSITION_X += delta_x
        self.SHADOW_TARGET_POSITION_Y += delta_y

        self.glass.pos = (new_glass_x, new_glass_y)
        self.shadow.move_by_delta(delta_x, delta_y)

        self._update_point_a_marker()

    def _on_glass_drag_end(self, touch):
        if DEBUG_MODE:
            print("🔴 [DRAG_END] Вызван")
        if self.sound_glass_drag:
            self._fade_volume(0.0, 0.3)
        self.last_touch_pos = None
        self.last_touch_time = None

    def _on_glass_click(self):
        if self.is_glass_blocked:
            if DEBUG_MODE:
                print("🔒 [GLASS] Стакан заблокирован, клик игнорируется")
            return

        if self.is_animating:
            return

        if self.is_at_target:
            if self.dice_hidden:
                self.play_dice_roll_sound()

                SPEED_THRESHOLD = 300

                if self.max_speed > SPEED_THRESHOLD:
                    for dice in self.dice_list:
                        dice.set_random_frame()
                else:
                    for dice in self.dice_list:
                        dice.set_random_frame_same_row()

                self.max_speed = 0
                self.last_touch_pos = None
                self.last_touch_time = None

                for dice in self.dice_list:
                    dice.opacity = 1
                    if dice.glow:
                        dice.glow.opacity = 1
                self.dice_hidden = False
                self.pending_hide_dice = False

                for dice in self.dice_list:
                    dice.enable_glow()

                def after_glass_raise():
                    Clock.schedule_once(lambda dt: self._animate_dice_appearance(), 0.1)

                self._raise_glass(on_complete_callback=after_glass_raise)
            else:
                self._raise_glass()
        else:
            if self.is_dice_enlarged:
                self._shrink_all_dice()
                Clock.schedule_once(lambda dt: self._process_glass_lower(), 0.4)
            else:
                self._process_glass_lower()

    def _process_glass_lower(self):
        if self.dice_list and not self.dice_hidden:
            if len(self.dice_list) == 1:
                target_dice = self.dice_list[0]
                dice_center_x = target_dice.pos[0] + target_dice.width / 2
                dice_center_y = target_dice.pos[1] + target_dice.height / 2
            else:
                total_x = 0
                total_y = 0
                for dice in self.dice_list:
                    total_x += dice.pos[0] + dice.width / 2
                    total_y += dice.pos[1] + dice.height / 2
                dice_center_x = total_x / len(self.dice_list)
                dice_center_y = total_y / len(self.dice_list)

            current_point_a_x = self.glass_start_pos[0] + self.glass_size / 6.5
            current_point_a_y = self.glass_start_pos[1] + self.glass_size / 2

            distance_x = abs(current_point_a_x - dice_center_x)
            distance_y = abs(current_point_a_y - dice_center_y)

            if distance_x <= 50 and distance_y <= 50:
                self.pending_hide_dice = True
                self._lower_glass_to_center(dice_center_x, dice_center_y)
            else:
                self._lower_glass()
        else:
            self._lower_glass()

    def _disable_glow_for_all_dice(self):
        for dice in self.dice_list:
            dice.disable_glow()

    def _on_glass_move_complete(self):
        pass

    def _on_appearance_complete(self, dice):
        self.animation_counter += 1
        if self.animation_counter >= 2:
            self.is_animating = False
            self.animation_counter = 0

    def _get_dice_center(self):
        if not self.dice_list:
            if self.last_dice_center:
                return self.last_dice_center
            center_x = self.START_POSITION_DICE_X + self.large_dice_size // 2
            center_y = self.START_POSITION_DICE_Y + self.large_dice_size // 2
            return (center_x, center_y)

        if len(self.dice_list) == 1:
            dice = self.dice_list[0]
            center = (dice.pos[0] + dice.width / 2, dice.pos[1] + dice.height / 2)
            self.last_dice_center = center
            return center
        else:
            total_x = 0
            total_y = 0
            for dice in self.dice_list:
                total_x += dice.pos[0] + dice.width / 2
                total_y += dice.pos[1] + dice.height / 2
            center = (total_x / len(self.dice_list), total_y / len(self.dice_list))
            self.last_dice_center = center
            return center

    def _create_dice_for_mode(self, mode, animate=True):
        self._clear_all_dice()
        self.dice_hidden = False
        self.pending_hide_dice = False
        self.is_dice_enlarged = False

        if not animate:
            if mode == 1:
                dice = DiceWidget(
                    sprite_sheet_path=self.sprite_sheet_path,
                    dice_size=self.large_dice_size,
                    rows=6,
                    cols=12,
                    frame_index=0,
                    rotation_angle=-90,
                    size_hint=(None, None),
                    size=(self.large_dice_size, self.large_dice_size),
                    pos=(self.START_POSITION_DICE_X, self.START_POSITION_DICE_Y),
                    on_dice_click=self._on_dice_click
                )
                dice.set_random_frame()
                dice.original_position = dice.pos
                dice.original_size = dice.dice_size
                self.layout.add_widget(dice)
                self.dice_list.append(dice)

            elif mode == 2:
                distance_between = self.dice_size * 0.3
                center_y = self.START_POSITION_DICE_Y + (self.large_dice_size // 2) - (self.dice_size // 2)

                y_top = center_y - distance_between
                y_bottom = center_y + distance_between

                dice1 = DiceWidget(
                    sprite_sheet_path=self.sprite_sheet_path,
                    dice_size=self.dice_size,
                    rows=6,
                    cols=12,
                    frame_index=0,
                    rotation_angle=-90,
                    size_hint=(None, None),
                    size=(self.dice_size, self.dice_size),
                    pos=(self.START_POSITION_DICE_X, y_top),
                    on_dice_click=self._on_dice_click
                )
                dice1.original_position = dice1.pos
                dice1.original_size = dice1.dice_size

                dice2 = DiceWidget(
                    sprite_sheet_path=self.sprite_sheet_path,
                    dice_size=self.dice_size,
                    rows=6,
                    cols=12,
                    frame_index=0,
                    rotation_angle=-90,
                    size_hint=(None, None),
                    size=(self.dice_size, self.dice_size),
                    pos=(self.START_POSITION_DICE_X, y_bottom),
                    on_dice_click=self._on_dice_click
                )
                dice2.original_position = dice2.pos
                dice2.original_size = dice2.dice_size

                dice1.set_random_frame()
                dice2.set_random_frame()

                self.layout.add_widget(dice1)
                self.layout.add_widget(dice2)
                self.dice_list.append(dice1)
                self.dice_list.append(dice2)

                Clock.schedule_once(lambda dt: dice1._create_glow(), 0)
                Clock.schedule_once(lambda dt: dice2._create_glow(), 0)

            if self.glass and self.glass.parent:
                self.layout.remove_widget(self.glass)
                self.layout.add_widget(self.glass)
            return

        center = self._get_dice_center()

        if mode == 1:
            target_x = center[0] - self.large_dice_size / 2
            target_y = center[1] - self.large_dice_size / 2
            start_pos = (target_x, target_y)

            dice = DiceWidget(
                sprite_sheet_path=self.sprite_sheet_path,
                dice_size=self.large_dice_size,
                rows=6,
                cols=12,
                frame_index=0,
                rotation_angle=-90,
                size_hint=(None, None),
                size=(self.large_dice_size, self.large_dice_size),
                pos=start_pos,
                on_dice_click=self._on_dice_click
            )
            dice.set_random_frame()
            self.layout.add_widget(dice)
            self.dice_list.append(dice)

            dice.animate_appearance_from_center(
                (target_x, target_y),
                start_pos,
                self.appear_duration,
                None
            )

        elif mode == 2:
            distance_between = self.dice_size * 0.3

            y_top = center[1] - distance_between - self.dice_size / 2
            y_bottom = center[1] + distance_between - self.dice_size / 2
            dice_x = center[0] - self.dice_size / 2

            start_pos = (center[0] - self.dice_size / 2, center[1] - self.dice_size / 2)

            dice1 = DiceWidget(
                sprite_sheet_path=self.sprite_sheet_path,
                dice_size=self.dice_size,
                rows=6,
                cols=12,
                frame_index=0,
                rotation_angle=-90,
                size_hint=(None, None),
                size=(self.dice_size, self.dice_size),
                pos=start_pos,
                on_dice_click=self._on_dice_click
            )

            dice2 = DiceWidget(
                sprite_sheet_path=self.sprite_sheet_path,
                dice_size=self.dice_size,
                rows=6,
                cols=12,
                frame_index=0,
                rotation_angle=-90,
                size_hint=(None, None),
                size=(self.dice_size, self.dice_size),
                pos=start_pos,
                on_dice_click=self._on_dice_click
            )

            self.layout.add_widget(dice1)
            self.layout.add_widget(dice2)
            self.dice_list.append(dice1)
            self.dice_list.append(dice2)

            self.is_animating = True
            self.animation_counter = 0

            Clock.schedule_once(lambda dt: dice1._create_glow(), 0)
            Clock.schedule_once(lambda dt: dice2._create_glow(), 0)

            dice1.animate_appearance_from_center(
                (dice_x, y_top),
                start_pos,
                self.appear_duration,
                self._on_appearance_complete
            )
            dice2.animate_appearance_from_center(
                (dice_x, y_bottom),
                start_pos,
                self.appear_duration,
                self._on_appearance_complete
            )

        if self.glass and self.glass.parent:
            self.layout.remove_widget(self.glass)
            self.layout.add_widget(self.glass)

    def _start_switch_animation(self):
        if self.is_animating:
            return

        if self.is_dice_enlarged:
            self._shrink_all_dice()
            return

        self.is_animating = True
        self._get_dice_center()

        if self.current_mode == 1:
            self._animate_one_to_two()
        else:
            self._animate_two_to_one()

    def _animate_one_to_two(self):
        if not self.dice_list:
            self.is_animating = False
            return

        old_dice = self.dice_list[0]
        old_dice.animate_disappear_in_place(self.disappear_duration, None)

        appear_delay = self.disappear_duration - self.overlap_time
        Clock.schedule_once(lambda dt: self._create_small_dice(), appear_delay)

    def _create_small_dice(self):
        self._clear_all_dice()
        self.current_mode = 2
        self._create_dice_for_mode(2, animate=True)

    def _animate_two_to_one(self):
        if len(self.dice_list) < 2:
            self.is_animating = False
            return

        dice_top = self.dice_list[0]
        dice_bottom = self.dice_list[1]

        center = self._get_dice_center()
        center_pos = (center[0] - self.large_dice_size / 2, center[1] - self.large_dice_size / 2)

        dice_top.animate_disappear_to_center(center_pos, self.disappear_duration, None)
        dice_bottom.animate_disappear_to_center(center_pos, self.disappear_duration, None)

        appear_delay = self.disappear_duration - self.overlap_time
        Clock.schedule_once(lambda dt: self._create_big_dice(), appear_delay)

    def _create_big_dice(self):
        self._clear_all_dice()
        self.current_mode = 1
        self._create_dice_for_mode(1, animate=True)
        self.is_animating = False

    def _clear_all_dice(self):
        for dice in self.dice_list:
            if dice.parent:
                self.layout.remove_widget(dice)
        self.dice_list.clear()

    def go_to_menu(self):
        if self.volume_fade_clock:
            self.volume_fade_clock.cancel()
            self.volume_fade_clock = None
        if self.sound_glass_drag:
            try:
                self.sound_glass_drag.stop()
            except:
                pass
        self._clear_all_dice()
        if self.glass and self.glass.parent:
            self.layout.remove_widget(self.glass)
            self.glass = None
        if self.shadow and self.shadow.parent:
            self.layout.remove_widget(self.shadow)
            self.shadow = None
        if self.drop_zone and self.drop_zone.parent:
            self.layout.remove_widget(self.drop_zone)
            self.drop_zone = None
        if self.point_a_marker and self.point_a_marker.parent:
            self.layout.remove_widget(self.point_a_marker)
            self.point_a_marker = None
        self.play_back_sound()
        self.sound_manager.fade_to(1.0, duration=0.5)
        from main import switch_screen
        switch_screen('menu')