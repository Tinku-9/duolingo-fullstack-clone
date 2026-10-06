"""Windows Chrome CDP smoke test. Requires running frontend, backend and Chrome
with --headless=new --remote-debugging-port=9222 and an isolated profile.
Run against freshly seeded demo data. This completes lesson 3 for the demo user.
"""
import asyncio
import base64
import json
from pathlib import Path
from urllib.request import urlopen

from websockets.asyncio.client import connect

ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "artifacts"


class Browser:
    def __init__(self, socket):
        self.socket = socket
        self.counter = 0
        self.errors = []

    async def command(self, method, params=None):
        self.counter += 1
        call_id = self.counter
        await self.socket.send(json.dumps({"id": call_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(await self.socket.recv())
            if message.get("method") == "Runtime.exceptionThrown":
                self.errors.append(message["params"]["exceptionDetails"])
            if message.get("id") == call_id:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    async def evaluate(self, javascript):
        result = await self.command("Runtime.evaluate", {"expression": javascript, "returnByValue": True, "awaitPromise": True})
        if "exceptionDetails" in result:
            raise AssertionError(result["exceptionDetails"])
        return result.get("result", {}).get("value")

    async def wait(self, javascript, timeout=15):
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            if await self.evaluate(f"Boolean({javascript})"):
                return
            await asyncio.sleep(.2)
        raise AssertionError(f"Browser wait timed out: {javascript}; DOM: {await self.evaluate('document.body.innerText')}")

    async def click(self, selector, text=None):
        condition = f"x.textContent.trim() === {json.dumps(text)}" if text is not None else "true"
        await self.evaluate(f"(() => {{const element = [...document.querySelectorAll({json.dumps(selector)})].find(x => {condition}); if (!element || element.disabled) throw new Error('Unavailable control: ' + {json.dumps(selector + ' ' + str(text))}); element.click();}})()")

    async def type(self, value):
        await self.evaluate("document.querySelector('textarea').focus()")
        await self.command("Input.insertText", {"text": value})

    async def screenshot(self, filename):
        await asyncio.sleep(.3)
        result = await self.command("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False})
        ARTIFACTS.mkdir(exist_ok=True)
        (ARTIFACTS / filename).write_bytes(base64.b64decode(result["data"]))

    async def visit(self, path):
        await self.command("Page.navigate", {"url": "http://127.0.0.1:3000" + path})


async def run():
    targets = json.load(urlopen("http://127.0.0.1:9222/json"))
    target = next(x for x in targets if x["type"] == "page")
    async with connect(target["webSocketDebuggerUrl"], max_size=20_000_000) as socket:
        browser = Browser(socket)
        await browser.command("Runtime.enable")
        await browser.command("Page.enable")
        await browser.command("Emulation.setDeviceMetricsOverride", {"width": 1440, "height": 1000, "deviceScaleFactor": 1, "mobile": False})
        await browser.visit("/learn")
        await browser.wait("document.querySelectorAll('.path-node').length === 6")
        await browser.screenshot("learn-desktop.png")
        await browser.click(".path-node.available")
        await browser.click(".skill-popover .button")
        await browser.wait("document.querySelector('.choice-list')")
        await browser.click(".choice", "1no")
        await browser.click(".lesson-footer .button", "Check")
        await browser.wait("document.querySelector('.lesson-footer.incorrect')")
        await browser.screenshot("lesson-feedback.png")
        assert await browser.evaluate("document.querySelector('.lesson-header .stat').textContent.trim()") == "4"
        await browser.click(".lesson-footer .button", "Continue")
        await browser.wait("document.querySelector('.word-bank')")
        await browser.command("Page.reload")
        await browser.wait("document.querySelector('.word-bank')")
        for word in ("Yes,", "please"):
            await browser.click(".word-bank .word-token", word)
        await check_and_continue(browser)
        await browser.wait("document.querySelector('.match-grid')")
        for left, right in (("sí", "yes"), ("no", "no"), ("gracias", "thank you")):
            await browser.click(".match-grid > div:first-child .match-item", left)
            await browser.click(".match-grid > div:last-child .match-item", right)
        await check_and_continue(browser)
        await browser.wait("document.querySelector('.accent-buttons')")
        await browser.type("sí")
        await check_and_continue(browser)
        await browser.wait("document.querySelector('textarea') && !document.querySelector('.accent-buttons')")
        await browser.type("Yes, please")
        await check_and_continue(browser)
        await browser.wait("document.body.innerText.includes('Lesson complete!')")
        assert await browser.evaluate("document.body.innerText.includes('+20') && document.body.innerText.includes('80%')")
        await browser.screenshot("lesson-complete.png")
        await browser.click(".end-summary .button", "Continue")
        await browser.wait("document.querySelectorAll('.path-node').length === 6")
        for route, selector in (("/profile", ".achievement"), ("/leaderboard", ".leaderboard-row.you")):
            await browser.visit(route)
            await browser.wait(f"document.querySelector('{selector}')")
        await browser.command("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 1, "mobile": True})
        await browser.visit("/learn")
        await browser.wait("document.querySelectorAll('.path-node').length === 6")
        assert await browser.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Mobile horizontal overflow"
        await browser.screenshot("learn-mobile.png")
        await browser.click(".heart-button")
        await browser.wait("document.querySelector('[role=dialog]')")
        await browser.click(".modal .button", "Refill hearts")
        await browser.wait("!document.querySelector('[role=dialog]')")
        assert await browser.evaluate("document.querySelector('.heart-button').textContent.trim()") == "5"
        assert not browser.errors, browser.errors
        print("PASS: five exercise types, wrong feedback, refresh recovery, completion/XP, profile, leaderboard, mobile overflow and heart refill.")
        print("Screenshots saved to", ARTIFACTS)


async def check_and_continue(browser):
    await browser.click(".lesson-footer .button", "Check")
    await browser.wait("document.querySelector('.lesson-footer.correct')")
    await browser.click(".lesson-footer .button", "Continue")


if __name__ == "__main__":
    asyncio.run(run())
