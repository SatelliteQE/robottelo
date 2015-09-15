# -*- encoding: utf-8 -*-
"""
Templates for generic positive/negative CRUD tests.
"""
from robottelo.cli.base import CLIReturnCodeError


def test_positive_create(self, data):
    """
    Successfully creates object FOREMAN_OBJECT.

    1. Create a new Foreman object using the a base factory using
       B{@data} as argument;
    2. Assert that the object was created and can be found;

    @type data: dictionary
    @param data: A python dictionary representing a Foreman CLI object.

    @rtype: assertion
    @return: Asserts that object can be created.
    """

    # Create a new object passing @data to factory method
    new_obj = self.factory(data)

    # Can we find the new object?
    result = self.factory_obj().exists(
        search=(self.search_key, new_obj[self.search_key])
    )

    self.assertEqual(new_obj[self.search_key], result[self.search_key])


def test_negative_create(self, data):
    """
    Fails to creates object FOREMAN_OBJECT.

    1. Create a new Foreman object using the a base factory using
       B{@data} as argument;
    2. Assert that the object was not created;

    @type data: dictionary
    @param data: A python dictionary representing a Foreman CLI object, with
    values that should cause an exception or be invalid.

    @rtype: assertion
    @return: Asserts that object can not be created.
    """

    # Try to create a new object passing @data to factory method
    with self.assertRaises(CLIReturnCodeError):
        self.factory_obj().create(data)


def test_positive_update(self, data):
    """
    Successfully updates object FOREMAN_OBJECT.

    1. Create a new Foreman object using the test base factory using
       B{@data}[1] as argument;
    2. Assert that the object was created and can be found;
    3. Update object using B{@data}[2] as updated values;
    4. Assert that the original object has new updates;

    @type data: tuple
    @param data: A tuple made up of two python dictionaries, where the first
    item contains the data for creation, and the second item represents the
    fields to be updated.

    @rtype: assertion
    @return: Asserts that object can be updated.
    """

    # "Unpacks" values from tuple
    orig_dict, updates_dict = data

    # Create a new object passing @data to factory method
    new_obj = self.factory(orig_dict)

    result = self.factory_obj().exists(
        search=(self.search_key, new_obj[self.search_key])
    )
    self.assertEqual(new_obj[self.search_key], result[self.search_key])

    # Store the new object for future assertions and to use its ID
    new_obj = result

    # Update original data with new values
    orig_dict['id'] = result['id']
    orig_dict.update(updates_dict)
    # Now update the Foreman object
    self.factory_obj().update(orig_dict)

    result = self.factory_obj().info({'id': new_obj['id']})

    # Verify that standard values are correct
    self.assertEqual(new_obj['id'], result['id'], 'IDs should match')
    self.assertNotEqual(
        new_obj[self.search_key], result[self.search_key])
    # There should be some attributes changed now
    self.assertNotEqual(new_obj, result, 'Object should be updated')


def test_negative_update(self, data):
    """
    Fails to update object FOREMAN_OBJECT after its creation.

    1. Create a new Foreman object using the test base factory using
       B{@data} as argument;
    2. Assert that the object was created and can be found;
    3. Update object using B{@data}[2] as updated values;
    4. Assert that the original object was not updated;

    @type data: dictionary
    @param data: A tuple made up of two python dictionaries, where the first
    item contains the data for creation, and the second item represents the
    fields to be updated with values that should cause an exception or be
    invalid.

    @rtype: assertion
    @return: Asserts that object is not updated.
    """

    # "Unpacks" values from tuple
    orig_dict, updates_dict = data

    # Create a new object passing @data to factory method
    new_obj = self.factory(orig_dict)

    result = self.factory_obj().exists(
        search=(self.search_key, new_obj[self.search_key])
    )
    self.assertEqual(new_obj[self.search_key], result[self.search_key])

    # Store the new object for future assertions and to use its ID
    new_obj = result

    # Update original data with new values
    orig_dict['id'] = int(result['id'])
    orig_dict.update(updates_dict)
    # Now update the Foreman object
    with self.assertRaises(CLIReturnCodeError):
        self.factory_obj().update(orig_dict)

    result = self.factory_obj().exists(
        search=(self.search_key, new_obj[self.search_key])
    )
    # Verify that new values were not updated
    self.assertEqual(new_obj, result, 'Object should not be updated')


def test_positive_delete(self, data):
    """
    Successfully deletes object FOREMAN_OBJECT.

    1. Create a new Foreman object using the test base factory using
       B{@data} as argument;
    2. Assert that the object was created and can be found;
    3. Delete an object using the correct ID from created object;
    4. Assert that the original object can no longer be found in the system;

    @type data: dictionary
    @param data: A python dictionary representing a Foreman CLI object.

    @rtype: assertion
    @return: Asserts that object can be created.
    """

    # Create a new object passing @data to factory method
    new_obj = self.factory(data)

    result = self.factory_obj().exists(
        search=(self.search_key, new_obj[self.search_key])
    )

    # Store the new object for future assertionss and to use its ID
    new_obj = result

    # Now delete it...
    self.factory_obj().delete({'id': new_obj['id']})
    # ... and make sure it does not exist anymore
    with self.assertRaises(CLIReturnCodeError):
        self.factory_obj().info({'id': new_obj['id']})


def test_negative_delete(self, data):
    """
    Fails to delete object FOREMAN_OBJECT shortly after its creation.

    1. Create a new Foreman object using the test base factory without
       arguments;
    2. Assert that the object was created and can be found;
    3. Delete an object using an incorrect ID from B{@data};
    4. Assert that the original object can still be found in the system;

    @type data: dictionary
    @param data: A python dictionary representing a Foreman CLI object with
    incorrect IDs.
    @rtype: assertion
    @return: Asserts that object is not deleted after its creation.
    """

    # Create a new object using default values
    new_obj = self.factory()

    result = self.factory_obj().exists(
        search=(self.search_key, new_obj[self.search_key])
    )
    # Store the new object for further assertions
    new_obj = result

    # Now try to delete it...
    with self.assertRaises(CLIReturnCodeError):
        self.factory_obj().delete(data)
    # Now make sure that it still exists

    result = self.factory_obj().exists(
        search=(self.search_key, new_obj[self.search_key])
    )
    self.assertEqual(new_obj, result)
