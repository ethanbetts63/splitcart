import { buildStaticPageGraph, metadataFor } from '@/lib/seo';
import StructuredDataScript from '@/components/seo/StructuredDataScript';

export const metadata = metadataFor('/privacy');

export default function PrivacyPage() {
  return (
    <main className="bg-surface-page">
      <StructuredDataScript structuredData={buildStaticPageGraph('/privacy')} />
      <div className="site-shell max-w-measure-wide px-6 py-12">
        <h1 className="text-display font-bold text-text-primary">Privacy Policy</h1>
        <p className="mt-3 text-body text-text-muted">Last updated: May 11, 2026</p>

        <div className="mt-8 space-y-8 text-text-control">
          <section>
            <h2 className="text-title-sm font-semibold text-text-primary">Overview</h2>
            <p className="mt-3">
              SplitCart helps compare grocery prices and optimise shopping lists. This policy
              explains the information we collect, how we use it, and the choices available to you.
            </p>
          </section>

          <section>
            <h2 className="text-title-sm font-semibold text-text-primary">
              Information We Collect
            </h2>
            <p className="mt-3">
              We may collect information you provide directly, such as account details, shopping
              list contents, selected stores, contact details, and messages sent to us. We may also
              collect basic technical information such as device, browser, page view, and usage
              data.
            </p>
          </section>

          <section>
            <h2 className="text-title-sm font-semibold text-text-primary">
              How We Use Information
            </h2>
            <p className="mt-3">
              We use information to provide the SplitCart service, optimise carts, save user
              preferences, improve the product, troubleshoot issues, respond to enquiries, and
              understand aggregate site usage.
            </p>
          </section>

          <section>
            <h2 className="text-title-sm font-semibold text-text-primary">Analytics</h2>
            <p className="mt-3">
              We use analytics tools to understand page views and site usage. Analytics data is used
              to improve performance, content, and user experience.
            </p>
          </section>

          <section>
            <h2 className="text-title-sm font-semibold text-text-primary">Sharing Information</h2>
            <p className="mt-3">
              We do not sell personal information. We may share information with service providers
              that help operate SplitCart, or where required by law.
            </p>
          </section>

          <section>
            <h2 className="text-title-sm font-semibold text-text-primary">Contact</h2>
            <p className="mt-3">For privacy questions, contact us at ethanbetts63@gmail.com.</p>
          </section>
        </div>
      </div>
    </main>
  );
}
