
import React from 'react';
import { Card, Accordion, Table, Row, Col } from 'react-bootstrap';

const OptimizationResultTile = ({ result, baselineCost }) => {
    return (
        <Accordion>
            <Card className="mb-3">
                <Accordion.Item eventKey="0">
                    <Accordion.Header>
                        <div className="w-100">
                            <Row>
                                <Col>
                                    <h5 className="mb-0">{result.max_stores} Store Option</h5>
                                </Col>
                                <Col className="text-right">
                                    <p className="mb-0">Optimized Cost: <span className="font-weight-bold text-primary">${result.optimized_cost.toFixed(2)}</span></p>
                                    <p className="mb-0">Savings: <span className="font-weight-bold text-success">${result.savings.toFixed(2)}</span></p>
                                </Col>
                            </Row>
                        </div>
                    </Accordion.Header>
                    <Accordion.Body>
                        {Object.entries(result.shopping_plan).map(([storeName, items]) => (
                            items.length > 0 && (
                                <div key={storeName} className="mb-4">
                                    <h6 className="font-weight-bold">{storeName}</h6>
                                    <Table striped bordered hover responsive="sm">
                                        <thead>
                                            <tr>
                                                <th>Product</th>
                                                <th>Brand</th>
                                                <th>Size</th>
                                                <th className="text-right">Price</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {items.map((item, itemIndex) => (
                                                <tr key={itemIndex}>
                                                    <td>{item.product_name}</td>
                                                    <td>{item.brand}</td>
                                                    <td>{item.sizes.join(', ')}</td>
                                                    <td className="text-right font-mono">${item.price.toFixed(2)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </Table>
                                </div>
                            )
                        ))}
                    </Accordion.Body>
                </Accordion.Item>
            </Card>
        </Accordion>
    );
};

export default OptimizationResultTile;
