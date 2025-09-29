import React from 'react';
import { Container, Row, Col, Button, Spinner } from 'react-bootstrap';
import ProductTile from './ProductTile';
import { useInfiniteQuery } from '@tanstack/react-query';

const ProductGrid = ({ searchTerm, userLocation }) => {

  const fetchProducts = async ({ pageParam = '/api/products/' }) => {
    let url = pageParam;
    // If the URL is a full URL (e.g., from lastPage.next), strip the domain
    if (url.startsWith('http')) {
      try {
        const urlObj = new URL(url);
        url = urlObj.pathname + urlObj.search;
      } catch (e) {
        console.error("Invalid URL in pageParam:", url, e);
        // Fallback to original url if parsing fails
      }
    }

    const params = new URLSearchParams();

    // Only append search and location params if it's the initial fetch (pageParam is the base URL)
    // or if they are not already part of the pageParam (which would be a 'next' URL)
    if (pageParam === '/api/products/') {
      if (searchTerm) {
        params.append('search', searchTerm);
      }
      if (userLocation && userLocation.postcode && userLocation.radius) {
        params.append('postcode', userLocation.postcode);
        params.append('radius', userLocation.radius);
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
    queryKey: ['products', searchTerm, userLocation],
    queryFn: fetchProducts,
    getNextPageParam: (lastPage) => lastPage.next,
    initialPageParam: '/api/products/',
  });

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
      {hasNextPage && (        <div className="text-center my-4">
          <Button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
            {isFetchingNextPage ? <Spinner animation="border" size="sm" /> : 'Load More'}
          </Button>
        </div>
      )}
    </Container>
  );
};

export default ProductGrid;
