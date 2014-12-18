iterstuff
=========

**Useful tools for working with iterators**

This package contains three useful tools to work with iterables in Python. They're
most useful for generators.

If the python2 `itertools` module is the Swiss Army Knife of functions for
iterables, `iterstuff` is the cut-down 2-blade version that you can keep on
your keyring.

## Lookahead

The Lookahead class 'wraps' an iterable and allows:

* Detection of the end of the generator using the `atend` property
* 'Peeking' at the next item to be yielded using the `peek` property

We'll look at use-cases in a moment, but first usage:

    >>> # Create a generator that will yield three integers
    >>> g = xrange(3)
    >>> # Wrap it in a Lookahead
    >>> from iterstuff import Lookahead
    >>> x = Lookahead(g)
    
Now we can use the properties of the Lookahead to check whether we're at the
start and/or end of the generator sequence, and to look at the next element
that would be yielded:

    >>> x.atstart
    True
    >>> x.atend
    False
    >>> x.peek
    0
    
Let's grab the first element and see how the properties change:

    >>> x.next()
    0
    >>> x.atstart
    False
    >>> x.atend
    False
    x.peek
    1
    
We have two ways to iterate over a sequence wrapped in a Lookahead:

    >>> # The usual way
    >>> x = Lookahead(xrange(3))
    >>> for y in x: print y
    0
    1
    2

    >>> # By checking for the end of the sequence
    >>> x = Lookahead(xrange(3))
    >>> while not x.atend:
    ...     y = x.next()
    ...     print y
    ...     
    0
    1
    2

The obvious question is: _why is this useful?_

### Repeating a `takewhile`

The [itertools.takewhile](https://docs.python.org/2/library/itertools.html#itertools.takewhile) function
can yield items from an iterable while some condition is satisfied. However,
it only yields items up until the condition is no longer satisfied, then it
stops, **after** testing the next element. Let's see what happens if we
want to use it to break a sequence of characters into letters and digits.

    >>> from itertools import takewhile
    >>> # Build a generator that returns a sequence
    >>> data = (x for x in 'abcd123ghi')
    >>> type(data)
    <type 'generator'>
    >>>
    >>> # Ok, let's get the characters that are not digits
    >>> print list(takewhile(lambda x: not x.isdigit(), data))
    ['a', 'b', 'c', 'd']
    >>> 
    >>> # Great, now let's get the digits
    >>> print list(takewhile(lambda x: x.isdigit(), data))
    ['2', '3']

What happened to '1'? When we were taking the non-digits, the `takewhile`
function took it from `data`, passed it to the `lambda` and when that returned
False, terminated. But of course, by then the '1' had already been consumed,
so when we started the second `takewhile`, the first character it got was '2'.

We can solve this with a Lookahead. Here's a 'repeatable takewhile' equivalent
(which is in the module):

    def repeatable_takewhile(predicate, iterable):
        """
        Like itertools.takewhile, but does not consume the first
        element of the iterable that fails the predicate test.
        """
        
        # Assert that the iterable is a Lookahead. The act of wrapping
        # an iterable in a Lookahead consumes the first element, so we
        # cannot do the wrapping inside this function.
        if not isinstance(iterable, Lookahead):
            raise TypeError("The iterable parameter must be a Lookahead")
        
        # Use 'peek' to check if the next element will satisfy the
        # predicate, and yield while this is True, or until we reach
        # the end of the iterable.
        while (not lah.atend) and predicate(lah.peek):
            yield lah.next()

Let's see how this behaves:

    >>> from iterstuff import repeatable_takewhile
    >>> data = Lookahead(iter('abcd123ghi'))
    Traceback (most recent call last):
      File "<input>", line 1, in <module>
    NameError: name 'Lookahead' is not defined
    >>> from iterstuff import repeatable_takewhile, Lookahead
    >>> data = Lookahead(x for x in 'abcd123ghi')
    >>> print list(repeatable_takewhile(lambda x: not x.isdigit(), data))
    ['a', 'b', 'c', 'd']
    >>> print list(repeatable_takewhile(lambda x: x.isdigit(), data))
    ['1', '2', '3']

### Examine data before it's used

The *pandas* library can build a `DataFrame` from almost any sequence of
records. The `DataFrame` constructor checks the first record to determine the
data types of the columns. If we pass a generator `data` to the `DataFrame`
constructor, almost the first thing that happens is that `data` is turned into
a list, so that *pandas* can access `data[0]` to examine the data types. If
your generator yields many records, though, this is bad - it's just built a
list of those many records in memory, effectively doubling the amount of
memory used (memory to hold the list plus memory to hold the DataFrame).

A Lookahead allows code to peek ahead at the next row. So we could do the
same job as *pandas* in a different way:

    # Wrap the data in a Lookahead so we can peek at the first row
    peekable = Lookahead(data)
    
    # If we're at the end of the Lookahead, there's no data
    if peekable.atend:
        return
        
    # Grab the first row so we can look at the data types
    first_row = peekable.peek
    
    # ...process the data types...

### Simple `pairwise`
    
There's a beautiful recipe in the `itertools` documentation for yielding
pairs from an iterable:

    def pairwise(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        a, b = tee(iterable)
        next(b, None)
        return izip(a, b)

Beautiful, but a little complex. We can make a simpler version with a
Lookahead:

    def pairwise(iterable):
        "s -> (s0,s1), (s1,s2), (s2, s3), ..."
        lah = Lookahead(iterable)
        while not lah.atend:
            yield lah.next(), lah.peek

Let's try it:

    >>> data = iter('abcd123ghi')
    >>> print list(pairwise(data))
    [('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', '1'), ('1', '2'), ('2', '3'), ('3', 'g'), ('g', 'h'), ('h', 'i'), ('i', None)]

### Chunking

Chunking is like using the repeatable `takewhile`, but for a specific use-case.

Suppose you're reading data from a database: the results of a big query over a
LEFT OUTER JOIN between several tables. Let's create a simplified (but
real-world) example.

We store data that relates to timing of web pages. We store an `event` for
each page, and for each event we store multiple `value`s. Our tables look
something like:

    Event
    ID  Created             Session URL
    01  2014-12-17 01:00:00 ab12f43 http://www.mobify.com/
    02  2014-12-17 01:00:01 ab12f43 http://www.mobify.com/jobs
    ...and so on for millions of events...
    
    Value
    Event_ID  Name              Value
    01        DOMContentLoaded     83
    01        Load                122
    02        DOMContentLoaded     64
    02        Load                345
    ...and so on for millions of values for millions of events...
    
At the end of every day, we process the records for that day, by doing a
query like:

    SELECT *
    FROM Event LEFT OUTER JOIN Value ON Event.ID = Value.Event_ID
    ORDER BY Event.ID

We'll probably end up with something like a SQLAlchemy `ResultProxy` or a
Django `QuerySet` - an iterable thing that yields records (and here we're
assuming that your database will stream the results back to your Python
client so that you can process much more data than you could ever fit into
memory). Let's call that iterable thing `records`.

What we want to do is to process each event. The problem is that if we just
iterate over the `records`:

    for record in records:
        print record.ID, record.Created, record.Name, record.Value

...we'll get one record per **value** - more than one record per **event**:

    01 2014-12-17 01:00:00 DOMContentLoaded 83
    01 2014-12-17 01:00:00 Load 122
    02 2014-12-17 01:00:01 DOMContentLoaded 64
    02 2014-12-17 01:00:01 Load 345

We could use the `repeatable_takewhile` to grab all the records belonging
to the same event:

    lah = Lookahead(records)
    
    while not lah.atend:
        current_event_id = lah.peek.ID
        event_records = list(
            repeatable_takewhile(
                lambda r: r.ID == current_event_id,
                lah
            )
        )
        
        # Now we have just the records for the next event
        ...process...
        
Because this is a common use case, Lookahead has a helper function to
make this even easier. The `Lookahead.chunked` staticmethod takes a function
to extract a 'key' value from each element, and yields successive
iterables, each of which has records with the same key value.

    for records_for_events in Lookahead.chunked(
            records,
            lambda r: r.ID
        ):
        # records_for_events is a sequence of records for
        # one event.
        ...process...

In fact, we can use chunking in the character class problem we showed earlier:

    >>> data = (x for x in 'abcd123ghi')
    >>> for charset in Lookahead.chunked(data, lambda c: c.isdigit()):
    ...     print list(charset)
    ...     
    ['a', 'b', 'c', 'd']
    ['1', '2', '3']
    ['g', 'h', 'i']

## Batching

The `batch` method is a simplification of a common use for `itertools.islice`.

Suppose your generator yields records that you're reading from a file, or a
database. Suppose that there may be many hundreds of thousands of records, or
even millions, so you can't fit them all into memory. You need to do them in
batches of 1000.

One way to iterate over the records would be something like:

    from itertools import islice
    CHUNK = 1000
    while True:
        # Listify the records so that we can check if
        # there were any returned.
        chunk = list(islice(records, CHUNK))
        if not chunk:
            break
        
        # Process the records in this chunk
        for record in chunk:
            process(record)

Or the iterstuff `batch` function will do this for you:

    from iterstuff import batch
    CHUNK = 1000
    for chunk in batch(records, CHUNK):
        # Chunk is an iterable of up to CHUNK records
        for record in chunk:
            process(record)
    
