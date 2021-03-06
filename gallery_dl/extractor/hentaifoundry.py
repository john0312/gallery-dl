# -*- coding: utf-8 -*-

# Copyright 2015-2017 Mike Fährmann
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.

"""Extract images from https://www.hentai-foundry.com/"""

from .common import Extractor, Message
from .. import text, exception


class HentaifoundryUserExtractor(Extractor):
    """Extractor for all images of a hentai-foundry-user"""
    category = "hentaifoundry"
    subcategory = "user"
    directory_fmt = ["{category}", "{artist}"]
    filename_fmt = "{category}_{index}_{title}.{extension}"
    pattern = [
        (r"(?:https?://)?(?:www\.)?hentai-foundry\.com/"
         r"pictures/user/([^/]+)/?$"),
        (r"(?:https?://)?(?:www\.)?hentai-foundry\.com/"
         r"user/([^/]+)/profile"),
    ]
    test = [
        ("https://www.hentai-foundry.com/pictures/user/Tenpura", {
            "url": "ebbc981a85073745e3ca64a0f2ab31fab967fc28",
            "keyword": "6e9a549feb9bafebd9d9342ef3c8ccad33a7031c",
        }),
        ("http://www.hentai-foundry.com/user/asdq/profile", {
            "exception": exception.NotFoundError,
        }),
    ]
    url_base = "https://www.hentai-foundry.com/pictures/user/"

    def __init__(self, match):
        Extractor.__init__(self)
        self.artist = match.group(1)

    def items(self):
        data, token = self.get_job_metadata()
        self.set_filters(token)
        yield Message.Version, 1
        yield Message.Directory, data
        for url, image in self.get_images():
            image.update(data)
            yield Message.Url, url, image

    def get_images(self):
        """Yield url and keywords for all images of one artist"""
        num = 1
        needle = 'thumbTitle"><a href="/pictures/user/'
        while True:
            pos = 0
            url = self.url_base + self.artist + "/page/" + str(num)
            page = self.request(url).text
            for _ in range(25):
                part, pos = text.extract(page, needle, '"', pos)
                if not part:
                    return
                yield self.get_image_metadata(self.url_base + part)
            num += 1

    def get_job_metadata(self):
        """Collect metadata for extractor-job"""
        url = self.url_base + self.artist + "?enterAgree=1"
        response = self.session.get(url)
        if response.status_code == 404:
            raise exception.NotFoundError("user")
        page = response.text
        token, pos = text.extract(page, 'hidden" value="', '"')
        count, pos = text.extract(page, 'class="active" >Pictures (', ')', pos)
        return {"artist": self.artist, "count": count}, token

    def get_image_metadata(self, url):
        """Collect metadata for an image"""
        page = self.request(url).text
        offset = len(self.url_base) + len(self.artist)
        index = text.extract(url, '/', '/', offset)[0]
        title, pos = text.extract(
            page, 'Pictures</a> &raquo; <span>', '<')
        url, pos = text.extract(
            page, '//pictures.hentai-foundry.com', '"', pos)
        data = {"index": index, "title": text.unescape(title)}
        text.nameext_from_url(url, data)
        return "https://pictures.hentai-foundry.com" + url, data

    def set_filters(self, token):
        """Set site-internal filters to show all images"""
        formdata = {
            "YII_CSRF_TOKEN": token,
            "rating_nudity": 3,
            "rating_violence": 3,
            "rating_profanity": 3,
            "rating_racism": 3,
            "rating_sex": 3,
            "rating_spoilers": 3,
            "rating_yaoi": 1,
            "rating_yuri": 1,
            "rating_teen": 1,
            "rating_guro": 1,
            "rating_furry": 1,
            "rating_beast": 1,
            "rating_male": 1,
            "rating_female": 1,
            "rating_futa": 1,
            "rating_other": 1,
            "rating_scat": 1,
            "rating_incest": 1,
            "rating_rape": 1,
            "filter_media": "A",
            "filter_order": "date_new",
            "filter_type": 0,
        }
        self.request("https://www.hentai-foundry.com/site/filters",
                     method="post", data=formdata)


class HentaifoundryImageExtractor(Extractor):
    """Extractor for a single image from hentaifoundry.com"""
    category = "hentaifoundry"
    subcategory = "image"
    directory_fmt = ["{category}", "{artist}"]
    filename_fmt = "{category}_{index}_{title}.{extension}"
    pattern = [(r"(?:https?://)?(?:www\.|pictures\.)?hentai-foundry\.com/"
                r"(?:pictures/user/([^/]+)/(\d+)"
                r"|[^/]/([^/]+)/(\d+))")]
    test = [
        (("http://www.hentai-foundry.com/"
          "pictures/user/Tenpura/407501/shimakaze"), {
            "url": "fbf2fd74906738094e2575d2728e8dc3de18a8a3",
            "keyword": "304479cfe00fbb723886be78b2bd6b9306a31d8a",
            "content": "91bf01497c39254b6dfb234a18e8f01629c77fd1",
        }),
        ("http://www.hentai-foundry.com/pictures/user/Tenpura/340853/", {
            "exception": exception.NotFoundError,
        }),
    ]

    def __init__(self, match):
        Extractor.__init__(self)
        self.artist = match.group(1) or match.group(3)
        self.index = match.group(2) or match.group(4)

    def items(self):
        url, data = self.get_image_metadata()
        yield Message.Version, 1
        yield Message.Directory, data
        yield Message.Url, url, data

    def get_image_metadata(self):
        """Collect metadata for an image"""
        url = "https://www.hentai-foundry.com/pictures/user/{}/{}".format(
            self.artist, self.index)
        response = self.session.get(url + "?enterAgree=1")
        if response.status_code == 404:
            raise exception.NotFoundError("image")
        extr = text.extract
        page = response.text
        artist, pos = extr(page, '<a href="/pictures/user/', '"')
        title , pos = extr(page, 'Pictures</a> &raquo; <span>', '<', pos)
        url   , pos = extr(page, '//pictures.hentai-foundry.com', '"', pos)
        data = {
            "artist": artist,
            "index": self.index,
            "title": text.unescape(title),
        }
        text.nameext_from_url(url, data)
        return "https://pictures.hentai-foundry.com" + url, data
