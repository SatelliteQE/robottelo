
def test_positive_create(self, data):
    """
    Successfully creates an object.
    """

    new_obj = self.factory(data)
    result = self.factory_obj().info(
        {self.search_key: new_obj[self.search_key]})

    # Dict keys start with upper case
    _dict_key = self.search_key[0].upper() + self.search_key[1:]
    self.assertEqual(new_obj[self.search_key], result.stdout[_dict_key])
    self.assertTrue(result.return_code == 0, "Failed to create object")
    self.assertTrue(len(result.stderr) == 0)


def test_negative_create(self, data):
    """
    Fails to creates object.
    """

    new_obj = self.factory_obj().create(data)
    self.assertNotEqual(new_obj.return_code, 0)
    self.assertIsNotNone(new_obj.stderr)


def test_positive_update(self, data):
    pass


def test_negative_update(self, data):
    pass


def test_positive_delete(self, data):
    """
    Successfully deletes an object
    """

    new_obj = self.factory(data)
    result = self.factory_obj().info(
        {self.search_key: new_obj[self.search_key]})
    self.assertTrue(result.return_code == 0, "Failed to create object")

    # Now delete it...
    result = self.factory_obj().delete(
        {self.search_key: new_obj[self.search_key]})
    self.assertTrue(result.return_code == 0, "Failed to delete object")
    self.assertTrue(len(result.stderr) == 0)
    # ... and make sure it does not exist anymore
    result = self.factory_obj().info(
        {self.search_key: new_obj[self.search_key]})
    self.assertFalse(result.return_code == 0, "Return code should not be zero")
    self.assertTrue(len(result.stderr) > 0, "Should have gotten an error")
    self.assertEqual(result.stdout, [], "Should not get any output")


def test_negative_delete(self, data):
    pass
