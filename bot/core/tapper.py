import asyncio
import random
import string
from time import time
from urllib.parse import unquote, quote

import aiohttp
import json
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw import types
from .agents import generate_random_user_agent
from bot.config import settings

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
from .helper import format_duration
from datetime import datetime
import pytz


class Tapper:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.user_id = 0
        self.username = None
        self.first_name = None
        self.last_name = None
        self.fullname = None
        self.start_param = None
        self.peer = None
        self.first_run = None

        self.session_ug_dict = self.load_user_agents() or []

        headers['User-Agent'] = self.check_user_agent()

    async def generate_random_user_agent(self):
        return generate_random_user_agent(device_type='android', browser_type='chrome')

    def info(self, message):
        from bot.utils import info
        info(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def debug(self, message):
        from bot.utils import debug
        debug(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def warning(self, message):
        from bot.utils import warning
        warning(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def error(self, message):
        from bot.utils import error
        error(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def critical(self, message):
        from bot.utils import critical
        critical(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def success(self, message):
        from bot.utils import success
        success(f"<light-yellow>{self.session_name}</light-yellow> | {message}")

    def save_user_agent(self):
        user_agents_file_name = "user_agents.json"

        if not any(session['session_name'] == self.session_name for session in self.session_ug_dict):
            user_agent_str = generate_random_user_agent()

            self.session_ug_dict.append({
                'session_name': self.session_name,
                'user_agent': user_agent_str})

            with open(user_agents_file_name, 'w') as user_agents:
                json.dump(self.session_ug_dict, user_agents, indent=4)

            logger.success(f"<light-yellow>{self.session_name}</light-yellow> | User agent saved successfully")

            return user_agent_str

    def load_user_agents(self):
        user_agents_file_name = "user_agents.json"

        try:
            with open(user_agents_file_name, 'r') as user_agents:
                session_data = json.load(user_agents)
                if isinstance(session_data, list):
                    return session_data

        except FileNotFoundError:
            logger.warning("User agents file not found, creating...")

        except json.JSONDecodeError:
            logger.warning("User agents file is empty or corrupted.")

        return []

    def check_user_agent(self):
        load = next(
            (session['user_agent'] for session in self.session_ug_dict if session['session_name'] == self.session_name),
            None)

        if load is None:
            return self.save_user_agent()

        return load

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            with_tg = True

            if not self.tg_client.is_connected:
                with_tg = False
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            # if settings.REF_ID == '':
            #     self.start_param = 'ref_QwD3tLsY8f'
            # else:
            #     self.start_param = settings.REF_ID

            peer = await self.tg_client.resolve_peer('notpixel')
            InputBotApp = types.InputBotAppShortName(bot_id=peer, short_name="app")

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotApp,
                platform='android',
                write_allowed=True
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0])

            try:
                if self.user_id == 0:
                    information = await self.tg_client.get_me()
                    self.user_id = information.id
                    self.first_name = information.first_name or ''
                    self.last_name = information.last_name or ''
                    self.username = information.username or ''
            except Exception as e:
                print(e)

            if with_tg is False:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(
                f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def login(self, http_client: aiohttp.ClientSession, initdata):
        try:

            resp = await http_client.get("https://notpx.app/api/v1/users/me", ssl=False)

            #self.debug(f'login text {await resp.text()}')
            resp_json = await resp.json()

            return resp_json

        except Exception as error:
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Login error {error}")
            return None, None

    async def claim(self, http_client: aiohttp.ClientSession):
        try:
            resp = await http_client.get("https://notpx.app/api/v1/mining/claim", ssl=False)
            if resp.status == 200:
                self.success(f"Successfully claim coins!")
            else:
                self.error(f"Can't do task!")

        except Exception as e:
            self.error(f"Error occurred during claim: {e}")

    async def paint(self, http_client: aiohttp.ClientSession, color: str):
        try:
            pixelId = random.randint(settings.PIXEL_IDS[0], settings.PIXEL_IDS[1])
            json_data = {"newColor": color, "pixelId": pixelId}

            resp = await http_client.post("https://notpx.app/api/v1/repaint/start", json=json_data, ssl=False)
            resp_json = await resp.json()
            return resp_json["balance"]
        except Exception as e:
            self.error(f"Error occurred during paint: {e}")

    async def get_status(self, http_client: aiohttp.ClientSession):
        try:
            resp = await http_client.get("https://notpx.app/api/v1/mining/status", ssl=False)
            resp_json = await resp.json()
            charges = resp_json.get("charges")
            user_balance = resp_json.get("userBalance")
            tasks = resp_json.get("tasks")
            boosts = resp_json.get("boosts")
            coins = resp_json.get("coins")

            return (charges,
                    user_balance, tasks, boosts, coins)
        except Exception as e:
            self.error(f"Error occurred during get status: {e}")

    async def upgrade_paint_reward(self, http_client: aiohttp.ClientSession):
        try:
            resp = await http_client.get("https://notpx.app/api/v1/mining/boost/check/paintReward", ssl=False)
            resp_json = await resp.json()
            paint_reward = resp_json.get("paintReward")

            if paint_reward:
                self.success(f"Successfully upgrade paint reward!")
            else:
                self.error(f"Can't upgrade paint reward!")

        except Exception as e:
            self.error(f"Error occurred during paint reward: {e}")

    async def upgrade_recharge_speed(self, http_client: aiohttp.ClientSession):
        try:
            resp = await http_client.get("https://notpx.app/api/v1/mining/boost/check/reChargeSpeed", ssl=False)
            resp_json = await resp.json()
            paint_reward = resp_json.get("reChargeSpeed")

            if paint_reward:
                self.success(f"Successfully upgrade recharge speed!")
            else:
                self.error(f"Can't upgrade recharge speed!")

        except Exception as e:
            self.error(f"Error occurred during recharge speed: {e}")

    async def upgrade_energy_limit(self, http_client: aiohttp.ClientSession):
        try:
            resp = await http_client.get("https://notpx.app/api/v1/mining/boost/check/energyLimit", ssl=False)
            resp_json = await resp.json()
            paint_reward = resp_json.get("energyLimit")

            if paint_reward:
                self.success(f"Successfully upgrade energy limit!")
            else:
                self.error(f"Can't upgrade energy limit!")

        except Exception as e:
            self.error(f"Error occurred during energy limit: {e}")

    async def check_task(self, http_client: aiohttp.ClientSession, task: str):
        task_url = ''
        if "x:" in task:
            if ':' in task:
                key, value = task.split(':')
                task_url = f"{key}?name={value}"
        else:
            task_url = task
        try:
            resp = await http_client.get(f"https://notpx.app/api/v1/mining/task/check/{task_url}", ssl=False)
            if resp.status == 200:
                self.success(f"Successfully do task {task}!")
            else:
                self.error(f"Can't do task!")

        except Exception as e:
            self.error(f"Error occurred during check task: {e}")

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Proxy: {proxy} | Error: {error}")

    async def run(self, proxy: str | None) -> None:
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        if proxy:
            await self.check_proxy(http_client=http_client, proxy=proxy)

        delay_account = random.randint(settings.DELAY_ACCOUNT[0], settings.DELAY_ACCOUNT[1])
        await asyncio.sleep(delay_account)

        while True:
            try:
                if "Authorization" in http_client.headers:
                    del http_client.headers["Authorization"]

                init_data = await self.get_tg_web_data(proxy=proxy)

                http_client.headers["Authorization"] = f"initData {init_data}"

                login_data = await self.login(http_client=http_client, initdata=init_data)
                if self.first_run is not True:
                    self.success("Logged in successfully!")
                    self.first_run = True


                charges, user_balance, tasks, boosts, coins = await self.get_status(http_client=http_client)
                self.info(f'Charges: {charges} | Balance: {user_balance}PX!')

                claim_tasks = [item for item in settings.TASKS if item not in tasks]
                for task in claim_tasks:
                    await self.check_task(http_client=http_client, task=task)
                    await asyncio.sleep(random.uniform(10, 15))

                if boosts.get('paintReward', 1) <= len(settings.PAINT_REWARDS_POINT) and user_balance > settings.PAINT_REWARDS_POINT[boosts.get('paintReward', 1) - 1]:
                    await self.upgrade_paint_reward(http_client=http_client)
                    charges, user_balance, tasks, boosts, coins = await self.get_status(http_client=http_client)
                    await asyncio.sleep(random.uniform(5, 10))

                if boosts.get('energyLimit', 1) <= len(settings.ENERGY_LIMIT_POINT) and user_balance > settings.ENERGY_LIMIT_POINT[boosts.get('energyLimit', 1) - 1]:
                    await self.upgrade_energy_limit(http_client=http_client)
                    charges, user_balance, tasks, boosts, coins = await self.get_status(http_client=http_client)
                    await asyncio.sleep(random.uniform(5, 10))

                if boosts.get('reChargeSpeed', 1) <= len(settings.RECHARGE_SPEED_POINT) and user_balance > settings.RECHARGE_SPEED_POINT[boosts.get('reChargeSpeed', 1) - 1]:
                    await self.upgrade_recharge_speed(http_client=http_client)
                    charges, user_balance, tasks, boosts, coins = await self.get_status(http_client=http_client)
                    await asyncio.sleep(random.uniform(5, 10))
                
                color = random.choice(settings.COLORS)
                while charges > 0:
                    balance = await self.paint(http_client=http_client, color=color)
                    self.success(f"Successfully paint | Balance: {balance}!")
                    await asyncio.sleep(random.uniform(0, 10))
                    charges -= 1

                if coins > 0.01:
                    await self.claim(http_client=http_client)

                current_time = datetime.now(pytz.timezone('Asia/Bangkok')).time()
                # Define start and end of night time (00:00 to 08:00 SGT)
                night_start = datetime.strptime("00:00", "%H:%M").time()
                night_end = datetime.strptime("06:00", "%H:%M").time()

                # Check if current time is within night time
                remaining_time = 0
                if night_start <= current_time < night_end and settings.SLEEP_BY_NIGHT_ENABLE:
                    # Calculate remaining time to 8 AM (in seconds)
                    remaining_time = (datetime.combine(datetime.today(), night_end) - datetime.combine(datetime.today(), current_time)).total_seconds() + random.randint(settings.SLEEP_BY_NIGHT[0], settings.SLEEP_BY_NIGHT[1])
                    self.info(f"Sleep by night {remaining_time}s!")
                else:
                    remaining_time = random.randint(settings.SLEEP[0], settings.SLEEP[1])
                    self.info(f"Sleep {remaining_time}s!")

                await asyncio.sleep(remaining_time)

            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Unknown error: {error}")
                await asyncio.sleep(delay=3)


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        await Tapper(tg_client=tg_client).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
