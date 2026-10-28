import math
from pathlib import Path

from pico2d import (
    SDL_KEYDOWN,
    SDL_KEYUP,
    SDLK_a,
    SDLK_LEFT,
    SDLK_RIGHT,
    SDLK_SPACE,
    get_time,
    load_image,
)
from transitions import Machine


class Boy:
    MIN_X = 50
    MAX_X = 750
    RUN_SPEED = 5
    AUTO_RUN_SPEED = 12
    AUTO_RUN_DURATION = 5
    AUTO_RUN_SCALE = 1.5

    def __init__(self):
        self.x, self.y = 400, 90
        self.frame = 0
        self.face_dir = 1
        self.pressed_directions = set()
        self.idle_started_at = get_time()
        self.auto_run_elapsed = 0
        self.auto_run_last_updated_at = get_time()
        self.is_invincible = False
        self.scale = 1
        self.image = load_image(str(Path(__file__).with_name('animation_sheet.png')))
        self.machine = Machine(
            model=self,
            states=['IDLE', 'RUN', 'SLEEP', 'AUTO_INVINCIBLE_RUN'],
            initial='IDLE',
            auto_transitions=False,
        )
        self.machine.add_transition('run', ['IDLE', 'SLEEP'], 'RUN')
        self.machine.add_transition('stop', 'RUN', 'IDLE', after='reset_idle_timer')
        self.machine.add_transition('sleep', 'IDLE', 'SLEEP')
        self.machine.add_transition('wake_up', 'SLEEP', 'IDLE', after='reset_idle_timer')
        self.machine.add_transition(
            'auto_run',
            'IDLE',
            'AUTO_INVINCIBLE_RUN',
            after='start_auto_run',
        )
        self.machine.add_transition(
            'auto_run_timeout',
            'AUTO_INVINCIBLE_RUN',
            'IDLE',
            after='end_auto_run',
        )
        self.machine.add_transition(
            'cancel_auto_run',
            'AUTO_INVINCIBLE_RUN',
            'RUN',
            after='cancel_auto_run_state',
        )

    def update(self):
        if self.state == 'IDLE':
            self.frame = (self.frame + 1) % 8
            if get_time() - self.idle_started_at >= 5:
                self.sleep()
        elif self.state == 'RUN':
            self.frame = (self.frame + 1) % 8
            self.x = max(
                self.MIN_X,
                min(self.MAX_X, self.x + self.face_dir * self.RUN_SPEED),
            )
        elif self.state == 'AUTO_INVINCIBLE_RUN':
            now = get_time()
            self.auto_run_elapsed += now - self.auto_run_last_updated_at
            self.auto_run_last_updated_at = now
            if self.auto_run_elapsed >= self.AUTO_RUN_DURATION:
                self.auto_run_timeout()
                return
            self.frame = (self.frame + 1) % 8
            self.x += self.face_dir * self.AUTO_RUN_SPEED
            if self.x >= self.MAX_X:
                self.x = self.MAX_X
                self.face_dir = -1
            elif self.x <= self.MIN_X:
                self.x = self.MIN_X
                self.face_dir = 1

    def handle_event(self, event):
        if event.type == SDL_KEYDOWN:
            if self.state == 'IDLE' and event.key == SDLK_a:
                self.auto_run()
            elif self.state == 'SLEEP' and event.key == SDLK_SPACE:
                self.wake_up()
            elif event.key in (SDLK_LEFT, SDLK_RIGHT):
                self.pressed_directions.add(event.key)
                self.face_dir = 1 if event.key == SDLK_RIGHT else -1
                if self.state == 'AUTO_INVINCIBLE_RUN':
                    self.cancel_auto_run()
                elif self.state in ('IDLE', 'SLEEP'):
                    self.run()
        elif event.type == SDL_KEYUP and event.key in (SDLK_LEFT, SDLK_RIGHT):
            self.pressed_directions.discard(event.key)
            if self.state == 'RUN' and not self.pressed_directions:
                self.stop()

    def reset_idle_timer(self):
        self.idle_started_at = get_time()

    def start_auto_run(self):
        self.auto_run_elapsed = 0
        self.auto_run_last_updated_at = get_time()
        self.is_invincible = True
        self.scale = self.AUTO_RUN_SCALE

    def end_auto_run(self):
        self.auto_run_elapsed = 0
        self.auto_run_last_updated_at = get_time()
        self.is_invincible = False
        self.scale = 1
        self.reset_idle_timer()

    def cancel_auto_run_state(self):
        self.auto_run_elapsed = 0
        self.auto_run_last_updated_at = get_time()
        self.is_invincible = False
        self.scale = 1

    def draw(self):
        if self.state == 'IDLE' and self.face_dir == 1:
            self.image.clip_draw(self.frame * 100, 300, 100, 100, self.x, self.y)
        elif self.state == 'IDLE':
            self.image.clip_draw(self.frame * 100, 200, 100, 100, self.x, self.y)
        elif self.state == 'RUN' and self.face_dir == 1:
            self.image.clip_draw(self.frame * 100, 100, 100, 100, self.x, self.y)
        elif self.state == 'RUN':
            self.image.clip_draw(self.frame * 100, 0, 100, 100, self.x, self.y)
        elif self.state == 'AUTO_INVINCIBLE_RUN' and self.face_dir == 1:
            self.image.clip_composite_draw(
                self.frame * 100,
                100,
                100,
                100,
                0,
                '',
                self.x,
                self.y,
                100 * self.scale,
                100 * self.scale,
            )
        elif self.state == 'AUTO_INVINCIBLE_RUN':
            self.image.clip_composite_draw(
                self.frame * 100,
                0,
                100,
                100,
                0,
                '',
                self.x,
                self.y,
                100 * self.scale,
                100 * self.scale,
            )
        elif self.face_dir == 1:
            self.image.clip_composite_draw(
                0, 300, 100, 100, math.pi / 2, '', self.x, self.y - 25, 100, 100
            )
        else:
            self.image.clip_composite_draw(
                0, 200, 100, 100, -math.pi / 2, '', self.x, self.y - 25, 100, 100
            )
