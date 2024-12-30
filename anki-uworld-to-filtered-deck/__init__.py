# JW Question IDs to Filtered Decks
#
# Copyright (C) 2022  Sachin Govind
# This is not my idea. There are existing addons that perform similar functionality - this addon is my implementation of that idea.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from aqt import mw
from aqt.qt import *
from aqt.utils import tooltip
from aqt import mw

from anki.collection import DYN_DUE, SearchNode
from anki.tags import TagTreeNode

from typing import Iterable

import re

config = mw.addonManager.getConfig(__name__)
JWTags = {}


def updateJWTags():
    # if we already gathered them, we're done
    if len(JWTags) > 0:
        return

    col = collection()
    tagTree = col.tags.tree()
    leafNodes = []

    def findLeafNodes(nodes: Iterable[TagTreeNode], baseName):
        for node in nodes:
            if node.children and len(node.children) > 0:
                findLeafNodes(node.children, baseName + "::" +
                              node.name if len(baseName) > 0 else node.name)
            else:
                leafNodes.append((node, baseName + "::" + node.name))

    findLeafNodes(tagTree.children, "")

    for nodePair in leafNodes:
        tagName = nodePair[1]
        if "::#JW::" in tagName:
            # parse qid
            qid = tagName.split("::")[-1]
            if not qid.isnumeric():
                continue
            qid = int(qid)
            JWTags[str(qid)] = tagName


def collection():
    collection = mw.col
    if collection is None:
        raise Exception('collection is not available')

    return collection


def _createFilteredDeckForJWQuestion(qid, fullTagName, parentDeckPath):
    if not fullTagName or len(fullTagName) < 2:
        return

    col = collection()
    search = col.build_search_string(SearchNode(tag=fullTagName))
    deckName = "JW #%s" % qid
    if len(parentDeckPath) > 0:
        deckName = parentDeckPath + "::" + deckName
    numberCards = 300

    # modifications based on config
    if config:
        if config["supplementalSearchText"]:
            search += " " + config["supplementalSearchText"]
        if config["numCards"] > 0:
            numberCards = config["numCards"]
        if config["unsuspendAutomatically"]:
            cidsToUnsuspend = col.find_cards(search)
            col.sched.unsuspend_cards(cidsToUnsuspend)

    did = col.decks.new_filtered(deckName)
    deck = col.decks.get(did)

    deck["terms"] = [[search, numberCards, DYN_DUE]]
    col.decks.save(deck)
    col.sched.rebuildDyn(did)


def _addJWFilteredDecks():
    qids, ok = QInputDialog.getText(
        mw, "JW Questions", "Enter a comma-separated list of JW question IDs: ")

    # canceled
    if not ok:
        return

    parsedQids = re.split('\W+', qids)
    if len(parsedQids) == 0:
        return

    parsedQids = [qid for qid in parsedQids if len(
        qid) > 0 and qid.isnumeric()]

    # build the JW tags array if it hasn't already been done
    updateJWTags()

    missedQids = []
    for qid in parsedQids:
        if str(qid) not in JWTags:
            missedQids.append(str(qid))
            continue
        tag = JWTags[qid]
        if not tag:
            missedQids.append(str(qid))
            continue

        _createFilteredDeckForJWQuestion(qid, tag, "JW")

    mw.reset()
    if len(missedQids) > 0:
        tooltip("No JW Tags for %s" % ",".join(missedQids), 10000)
    else:
        tooltip("Created filtered decks for all JW questions")


def _addJWFilteredDecksToTools():
    # Add our functions to the tools menu
    action = QAction("JW Filtered Decks", mw)
    qconnect(action.triggered, _addJWFilteredDecks)
    mw.form.menuTools.addAction(action)


_addJWFilteredDecksToTools()
