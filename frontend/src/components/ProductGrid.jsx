import React, { useEffect } from 'react';
import { Container, Row, Col, Button, Spinner } from 'react-bootstrap';
import ProductTile from './ProductTile';
import { useInfiniteQuery, useQueryClient } from '@tanstack/react-query';

const ProductGrid = ({ searchTerm, nearbyStoreIds }) => {
  const queryClient = useQueryClient();
  const queryKey = ['products', searchTerm, nearbyStoreIds];

  const getNextPageParam = (lastPage) => lastPage.next;

  const fetchProducts = async ({ pageParam = '/api/products/' }) => {
    // Check the cache first for a pre-fetched page
    const pageQueryKey = ['products-page', pageParam];
    const cachedPage = queryClient.getQueryData(pageQueryKey);
    if (cachedPage) {
      // If we find it, remove it from the single-page cache to save memory
      queryClient.removeQueries({ queryKey: pageQueryKey });
      return cachedPage;
    }

    let url = pageParam;
    if (url.startsWith('http')) {
      try {
        const urlObj = new URL(url);
        url = urlObj.pathname + urlObj.search;
      } catch (e) {
        console.error("Invalid URL in pageParam:", url, e);
      }
    }

    const params = new URLSearchParams();
    if (pageParam === '/api/products/') {
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      if (nearbyStoreIds && nearbyStoreIds.length > 0) {
        params.append('store_ids', nearbyStoreIds.join(','));
      }
    }

    if (params.toString() && pageParam === '/api/products/') {
      url += `?${params.toString()}`;
    }

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    return response.json();
  };

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    isError,
    error,
  } = useInfiniteQuery({
    queryKey: queryKey,
    queryFn: fetchProducts,
    getNextPageParam: getNextPageParam,
    initialPageParam: '/api/products/',
  });

  // Pre-fetch the next page as soon as the current one is loaded
  useEffect(() => {
    if (hasNextPage && !isFetchingNextPage) {
      const lastPage = data.pages[data.pages.length - 1];
      const nextPageParam = getNextPageParam(lastPage);
      if (nextPageParam) {
        const pageQueryKey = ['products-page', nextPageParam];
        queryClient.prefetchQuery({
          queryKey: pageQueryKey,
          queryFn: () => fetchProducts({ pageParam: nextPageParam }),
        });
      }
    }
  }, [data, hasNextPage, isFetchingNextPage, queryClient, fetchProducts]);

  if (isLoading) {
    return <Container className="text-center my-5"><Spinner animation="border" /></Container>;
  }

  if (isError) {
    return <Container className="text-center my-5 text-danger">Error: {error.message}</Container>;
  }

  const allProducts = data?.pages.flatMap(page => page.results) || [];
  const totalResults = data?.pages[0]?.count || 0;

  return (
    <Container fluid>
      {searchTerm && <h5 className="mb-3">Found {totalResults} results for "{searchTerm}"</h5>}
      <Row>
        {allProducts.length > 0 ? (
          allProducts.map((product) => (
            <Col key={product.id} sm={6} md={4} lg={3} className="mb-4">
              <ProductTile product={product} />
            </Col>
          ))
        ) : (
          <Col className="text-center my-5">No products found.</Col>
        )}
      </Row>

      {hasNextPage && (
        <div className="text-center my-4">
          <Button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
            {isFetchingNextPage ? <Spinner animation="border" size="sm" /> : 'Load More'}
          </Button>
        </div>
      )}
    </Container>
  );
};

export default ProductGrid;
