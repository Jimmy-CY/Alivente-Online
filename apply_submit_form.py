"""SV-1 - TWO SAVE BUTTONS THAT BELONGED TO NO FORM.

   Demetri, 5 Oct 2026: "If I edit an asset and I then select an invoice
   document and then press Save, nothing happens."

   Nothing happens because the button is not in the form.

       edit_asset.html line 23   <button type="submit" class="btn action-primary">
       edit_asset.html line 37   <form ... id="editAssetForm">

   A submit button that belongs to no form submits nothing. The browser
   swallows the click. There is no second Save on that page - the whole
   form body was checked.

   WHY IT LOOKED LIKE A FILE-UPLOAD BUG, which is the part worth writing
   down. Implicit submission: type in a text field, press Enter, and the
   browser submits the form directly, because the INPUTS are inside it.
   Every save ever made on that page went through Enter. Choosing a
   document means reaching for the mouse and clicking Save instead, and
   that path has never worked once.

   AND A SECOND ONE, which his report could not have found. Censusing
   every submit button in the tree against every form turned up exactly
   two orphans:

       edit_asset.html                Save Changes             line 23
       generate_lease_agreement.html  Generate Lease Agreement line 266

   #lease-generation-form contains zero submit controls, and nothing in
   that page calls .submit() or requestSubmit(). Its JS only toggles the
   button's `disabled` and its classes. So once country, language,
   property and tenant are chosen and the button goes live, clicking it
   does nothing either - and that page has no Enter fallback, because its
   controls are all <select>.

   THE FIX IS THE PATTERN THAT FILE ALREADY USES. edit_asset.html gets it
   right twice, on the per-photo buttons:

       <button type="submit" form="setCoverPhotoForm-{{ photo.id }}" ...>

   so the Save button takes the same attribute. The buttons stay where
   they are, in .page-action-buttons at the top, which is where every
   other screen in the app puts its actions. Demetri: "form= on both, and
   a suite that censuses the shape".

   FILES: edit_asset.html, generate_lease_agreement.html.
                                                 [test_submit_form.py]
"""
import os
import sys

import alv_tree as T

SUFFIX = '.bak_submitform'

# page, the button tag as it stands, the form it should have belonged to
TARGETS = [
    ('edit_asset.html',
     '<button type="submit" class="btn action-primary">',
     'editAssetForm'),
    ('generate_lease_agreement.html',
     '<button type="submit" class="btn action-primary btn-lg" '
     'id="generate-btn" disabled>',
     'lease-generation-form'),
]


def read(path):
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def backup(path):
    bak = path + SUFFIX
    if not os.path.exists(bak):
        with open(path, 'rb') as src, open(bak, 'wb') as dst:
            dst.write(src.read())


def main(argv):
    check = '--check' in argv
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    done = 0

    for name, tag, form_id in TARGETS:
        path = T.path_of(name)
        text = read(path)
        want = tag.replace('<button type="submit"',
                           '<button type="submit" form="%s"' % form_id, 1)
        if want in text:
            continue

        # THE ANCHOR MUST MATCH ONCE. A page can hold several buttons that
        # differ only in a class, and editing the second of two look-alikes
        # is worse than editing neither.
        n = text.count(tag)
        if n != 1:
            raise SystemExit('SV-1: the %s button matched %d times in %s, '
                             'expected 1' % (form_id, n, name))

        # AND THE FORM IT NAMES HAS TO BE THERE. A form= pointing at an id
        # that does not exist is the same defect wearing a fix.
        if ('id="%s"' % form_id) not in text:
            raise SystemExit('SV-1: %s has no form with id="%s"'
                             % (name, form_id))

        text = text.replace(tag, want, 1)
        if not check:
            backup(path)
            write(path, text)
        done += 1

    print('SV-1  buttons given their form : %d' % done)

    if check:
        if done:
            print('SV-1  NOT APPLIED')
            return 1
        print('SV-1  applied')
        return 0
    if done not in (0, len(TARGETS)):
        print('SV-1  REFUSED: partial application (%d of %d)'
              % (done, len(TARGETS)))
        return 2
    print('SV-1  ok')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
