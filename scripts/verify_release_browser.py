"""Exercise both roles against a disposable deployed build and optionally capture a demo."""
import argparse
import csv
from datetime import datetime
from io import StringIO
import json
import os
from pathlib import Path
import time
from uuid import uuid4
from zoneinfo import ZoneInfo

from playwright.sync_api import expect, sync_playwright

PASSWORD = 'Synthetic-account-test-only-4728'


def run(origin, artifacts=None, recording=False):
    today = datetime.now(ZoneInfo('Asia/Kolkata')).date().isoformat()
    source = os.getenv('GITHUB_SHA')
    errors = []
    if artifacts:
        artifacts.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        executable = os.getenv('BROWSER_EXECUTABLE')
        browser = playwright.chromium.launch(executable_path=executable)
        desktop = browser.new_context(viewport={'width': 1280, 'height': 900}, reduced_motion='reduce',
            **({'record_video_dir': str(artifacts / 'raw')} if recording else {}))
        page = desktop.new_page()
        page.on('pageerror', lambda err: errors.append(str(err)))
        start = time.monotonic()

        def button(title, root=page):
            return root.get_by_role('button', name=title, exact=True)

        def field(name, root=page):
            return root.get_by_label(name, exact=True)

        def chapter(seconds, title, summary, screenshot=None):
            if recording:
                page.evaluate('''([title, summary]) => {
                  let caption = document.getElementById('demo-caption');
                  if (!caption) {
                    caption = document.createElement('aside');
                    caption.id = 'demo-caption';
                    document.body.append(caption);
                  }
                  caption.textContent = title + '  •  ' + summary;
                  Object.assign(caption.style, {
                    position:'fixed', left:0, right:0, bottom:0, background:'#101b26',
                    color:'#fff', padding:'14px 20px', font:'16px system-ui', zIndex:99999,
                    pointerEvents:'none',
                  });
                }''', [title, summary])
                page.wait_for_timeout(max(0, seconds - (time.monotonic() - start)) * 1000)
            if screenshot and artifacts:
                page.evaluate("document.getElementById('demo-caption')?.remove()")
                page.screenshot(path=str(artifacts / screenshot), animations='disabled')

        def sign_up(email, role):
            button('Create an account').click()
            field('Email').fill(email)
            field('Password').fill(PASSWORD)
            field('Role').select_option(role)
            button('Create account and sign in').click()
            expect(button('Sign out')).to_be_visible()

        def switch(email):
            button('Sign out').click()
            field('Email').fill(email)
            field('Password').fill(PASSWORD)
            button('Sign in').click()
            expect(button('Sign out')).to_be_visible()
            expect(page.get_by_text(email, exact=True)).to_be_visible()

        def owner_records():
            button('Workers & wages').click()
            button('Open worker record').click()
            expect(page.get_by_role('heading', name='Wage ledger')).to_be_visible()

        def assignment():
            page.get_by_role('button', name='Jaipur test site · ' + today, exact=True).click()

        def balance(value):
            expect(page.locator('.live-totals div').filter(has_text='Closing balance')).to_contain_text(value)

        def open_earning(amount):
            row = page.locator('.live-list li').filter(has_text='Attendance · ' + amount)
            button('Entry details', row).click()
            panel = page.get_by_role('region', name='Ledger record details')
            expect(panel).to_be_visible()
            panel.scroll_into_view_if_needed()
            return panel

        page.goto(origin + '/#live', wait_until='networkidle')
        expect(page.get_by_role('heading', name='Sign in', exact=True)).to_be_visible()
        chapter(7, 'Worker Attendance & Wage Tracker', 'Local verification with synthetic accounts.', '01-live-signin.png')
        worker_email = f'worker-{uuid4().hex[:8]}@example.com'
        owner_email = f'contractor-{uuid4().hex[:8]}@example.com'
        sign_up(worker_email, 'worker')
        worker_id = page.locator('.live-account code').inner_text()
        button('Sign out').click()
        sign_up(owner_email, 'contractor')
        field('Name').fill('Unassigned test site')
        button('Create worksite').click()
        expect(button('Unassigned test site')).to_be_visible()
        field('Search worksites').fill('Unassigned')
        button('Unassigned test site').click()
        expect(page.get_by_role('heading', name='Edit worksite')).to_be_visible()
        field('Name').fill('Unassigned edited site')
        button('Save changes').click()
        expect(button('Unassigned edited site')).to_be_visible()
        button('Unassigned edited site').click()
        page.once('dialog', lambda dialog: dialog.accept())
        button('Delete worksite').click()
        expect(page.get_by_text('No worksites found.', exact=True)).to_be_visible()
        field('Search worksites').fill('')
        field('Name').fill('Jaipur test site')
        field('Location').fill('Synthetic demo data')
        button('Create worksite').click()
        expect(button('Jaipur test site')).to_be_visible()
        button('Workers & wages').click()
        field('Worker ID').fill(worker_id)
        button('Invite worker').click()
        expect(page.get_by_text(worker_email, exact=True)).to_be_visible()
        chapter(19, 'Invite a worker', 'A contractor creates a real worksite and sends a membership invitation.')
        switch(worker_email)
        button('Accept invitation').click()
        expect(page.get_by_role('heading', name='Assignments and agreed rates')).to_be_visible()
        chapter(28, 'Accept the invitation', 'The worker gives consent before the contractor can assign work.', '02-membership.png')
        switch(owner_email)
        owner_records()
        expect(field('Worksite')).to_be_visible()
        button('Create assignment').click()
        field('Daily rate (INR)').fill('600')
        button('Propose rate').click()
        expect(page.get_by_text('Awaiting worker', exact=False)).to_be_visible()
        button('Record attendance').click()
        expect(page.get_by_role('alert')).to_contain_text('needs worker acknowledgement')
        chapter(41, 'Propose ₹600 per day', 'Until the worker acknowledges the rate, attendance posting is blocked.')
        switch(worker_email)
        button('Open worker record').click()
        assignment()
        button('Acknowledge rate').click()
        expect(page.locator('.live-list li').filter(has_text='₹600.00').get_by_text('Agreed', exact=False)).to_be_visible()
        chapter(51, 'Worker agrees to the rate', 'The wage terms are saved with the worker’s acknowledgement.', '03-agreed-rate.png')
        switch(owner_email)
        owner_records()
        assignment()
        button('Record attendance').click()
        balance('₹600.00')
        field('Amount (INR)').fill('100')
        button('Save financial entry').click()
        balance('₹500.00')
        chapter(64, 'Post attendance and an advance', 'Full day earns ₹600. An advance of ₹100 leaves ₹500.', '04-wage-ledger.png')
        switch(worker_email)
        button('Open worker record').click()
        panel = open_earning('₹600.00')
        button('Acknowledge review', panel).click()
        expect(panel.get_by_text('Reviewed', exact=True).first).to_be_visible()
        field('Reason', panel).fill('Please correct this to a half day')
        button('Raise dispute', panel).click()
        expect(panel.get_by_text('Dispute open', exact=True).first).to_be_visible()
        balance('₹500.00')
        chapter(78, 'Worker disputes the attendance', 'The amount remains in the balance while the dispute is open.', '05-worker-dispute.png')
        switch(owner_email)
        owner_records()
        panel = open_earning('₹600.00')
        field('Response', panel).fill('Agreed. Replace the original with a half day.')
        field('Propose a correction', panel).check()
        field('Replacement attendance', panel).select_option('1')
        button('Send dispute response', panel).click()
        expect(panel.get_by_text('Correction proposed', exact=True).first).to_be_visible()
        balance('₹500.00')
        chapter(91, 'Contractor proposes a correction', 'The worker can accept or decline the proposal.')
        switch(worker_email)
        button('Open worker record').click()
        panel = open_earning('₹600.00')
        button('Submit dispute decision', panel).click()
        expect(panel.get_by_text('Resolved', exact=True).first).to_be_visible()
        balance('₹200.00')
        chapter(104, 'Worker resolves the dispute', 'The audit trail retains the original, its reversal, and a ₹300 replacement.', '06-resolved-dispute.png')
        with page.expect_download() as result:
            button('Download monthly CSV').click()
        download = result.value
        lines = list(csv.reader(StringIO(download.path().read_text())))
        assert dict(zip(lines[0], lines[1]))['closing_paise'] == '20000'
        assert any(row[1] == 'reversal' for row in lines[4:])
        assert desktop.request.get(origin + '/api/worksites').status == 401
        chapter(122, 'Export and reconcile', 'The monthly statement shows the same ₹200 closing balance as the live ledger.')
        video = page.video
        desktop.close()
        if recording:
            video.save_as(str(artifacts / 'recording.webm'))

        mobile = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        small = mobile.new_page()
        small.on('pageerror', lambda err: errors.append(str(err)))
        small.goto(origin + '/#live')
        small.get_by_label('Language').select_option('hi')
        expect(small.get_by_role('heading', name='साइन इन', exact=True)).to_be_visible()
        assert small.evaluate('document.documentElement.scrollWidth <= innerWidth')
        if artifacts:
            small.screenshot(path=str(artifacts / '07-hindi-mobile.png'), animations='disabled')
        mobile.close()
        browser.close()
    assert not errors, errors
    if artifacts:
        (artifacts / 'capture.json').write_text(json.dumps({
            'capture_date_ist': today, 'source_commit': source,
            'fixture': 'Synthetic worker and contractor in a disposable database',
            'checks': ['signup and login', 'worksite create, search, detail, edit and delete', 'invitation and assignment', 'acknowledged rate',
                       'attendance and advance', 'worker dispute and corrected ledger', 'monthly CSV',
                       'protected API', 'mobile Hindi login'],
        }, indent=2) + '\n')
    print('PASS: both browser roles, INR 200 reconciled correction and CSV, mobile Hindi login, no browser page errors')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8080')
    parser.add_argument('--artifacts', type=Path)
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    if args.record and not args.artifacts:
        parser.error('--record requires --artifacts')
    run(args.url.rstrip('/'), args.artifacts, args.record)
