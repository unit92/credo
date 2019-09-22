from xmldiff.patch import Patcher


class TrackedPatcher(Patcher):
    def __init__(self):
        return

    def patch(self, actions, tree):
        super().patch(actions, tree)

    def handle_action(self, action, tree):
        super.handle_action(action, tree)

    def _handle_DeleteNode(self, action, tree):
        super()._handle_DeleteNode(action, tree)

    def _handle_InsertNode(self, action, tree):
        super()._handle_InsertNode(action, tree)

    def _handle_RenameNode(self, action, tree):
        super()._handle_RenameNode(action, tree)

    def _handle_MoveNode(self, action, tree):
        super()._handle_MoveNode(action, tree)

    def _handle_UpdateTextIn(self, action, tree):
        super()._handle_UpdateTextIn(action, tree)

    def _handle_UpdateTextAfter(self, action, tree):
        super()._handle_UpdateTextAfter(action, tree)

    def _handle_UpdateAttrib(self, action, tree):
        super()._handle_UpdateAttrib(action, tree)

    def _handle_DeleteAttrib(self, action, tree):
        super()._handle_DeleteAttrib(action, tree)

    def _handle_InsertAttrib(self, action, tree):
        super()._handle_InsertAttrib(action, tree)

    def _handle_RenameAttrib(self, action, tree):
        super()._handle_RenameAttrib(action, tree)

    def _handle_InsertComment(self, action, tree):
        super()._handle_InsertComment(action, tree)
